"""Stage 4 tests: scheduler invariants, release dates, parent prerequisites, and worker apply scripts."""
import random
import sys
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from scripts import expand_v2_recurrence, propose_v2_replans
from v2.db import get_session
from v2.models import (
    Base,
    FocusSession,
    InAppNotification,
    PlanProposal,
    Preference,
    RecurrenceOccurrence,
    RecurrenceSeries,
    ScheduleBlock,
    Task,
    TaskDependency,
    User,
)
from v2.planner import BusyInterval, PlanPreview, PlanningPreferences, PlanningTask, ProposedBlock, preview_schedule
from v2.planning_api import get_preview, router as planning_router
from v2.priority import context_matches
from v2.replanning import MAX_CANDIDATES, _quality, _valid, choose_schedule


def _setup_db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


def test_scheduler_invariants_dst_release_date_and_randomized():
    now = datetime(2026, 11, 24, 8, tzinfo=timezone.utc)
    options = PlanningPreferences("UTC", time(8), time(18), 120, 0)

    # Deadline rescue
    tasks = [
        PlanningTask("later", "Later", 60, priority_score=90, deadline_at=now + timedelta(hours=3)),
        PlanningTask("urgent", "Urgent", 60, priority_score=50, deadline_at=now + timedelta(hours=1)),
    ]
    baseline = preview_schedule(tasks, [], options, now, 1)
    plan, _ = choose_schedule(tasks, [], options, now, 1)
    assert baseline.unscheduled and not plan.unscheduled
    assert plan.blocks[0].task_id == "urgent"

    # Release date / earliest_start_at prevents starting early
    future_task = PlanningTask(
        "fut", "Future", 30, priority_score=80, earliest_start_at=now + timedelta(days=1)
    )
    plan_rel, _ = choose_schedule([future_task], [], options, now, 2)
    assert len(plan_rel.blocks) == 1
    assert plan_rel.blocks[0].starts_at >= now + timedelta(days=1)

    # Validator rejects release date violation
    bad_block = ProposedBlock("fut", "Future", now, now + timedelta(minutes=30), 30)
    ok, errs = _valid(PlanPreview((bad_block,), ()), [], [future_task], options, now, 2)
    assert not ok and "RELEASE_DATE_VIOLATION" in errs

    # DST duration uses elapsed time
    zone = ZoneInfo("America/New_York")
    for dst_now in (datetime(2026, 3, 8, 0, tzinfo=zone), datetime(2026, 11, 1, 0, tzinfo=zone)):
        dst_opts = PlanningPreferences("America/New_York", time(0), time(5), 300, 0)
        dst_plan, _ = choose_schedule([PlanningTask("x", "X", 240)], [], dst_opts, dst_now, 1)
        for blk in dst_plan.blocks:
            elapsed = (blk.ends_at.astimezone(timezone.utc) - blk.starts_at.astimezone(timezone.utc)).total_seconds()
            assert elapsed == blk.duration_minutes * 60
        assert not dst_plan.unscheduled

    # Context word-boundary matching
    assert not context_matches("art", ["cartography"])
    assert context_matches("Placement Season", ["placement prep"])

    # Randomized feasibility & quality
    rng = random.Random(42)
    for _ in range(40):
        r_tasks = [
            PlanningTask(
                str(i), str(i), rng.choice([15, 30, 60, 90, 120]),
                priority_score=rng.randint(1, 100),
                deadline_at=now + timedelta(hours=rng.randint(1, 10)),
                splittable=rng.choice([True, False]),
            )
            for i in range(rng.randint(1, 8))
        ]
        r_opts = replace(options, min_break_minutes=rng.choice([0, 10, 15]))
        r_busy = [BusyInterval(now + timedelta(hours=2), now + timedelta(hours=3))]
        r_base = preview_schedule(r_tasks, r_busy, r_opts, now, 1)
        r_plan, trace = choose_schedule(r_tasks, r_busy, r_opts, now, 1)
        assert _valid(r_plan, r_busy, r_tasks, r_opts, now, 1)[0]
        assert _quality(r_plan, r_tasks) >= _quality(r_base, r_tasks)
        assert trace["candidates_checked"] <= MAX_CANDIDATES


def test_parent_prerequisite_inherited_and_recurrence_earliest_start_and_focus_noncompletion():
    engine = _setup_db()
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=2)).date()
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(Preference(owner_uid="alice", timezone="UTC", work_start=time(8), work_end=time(22)))
        db.flush()

        # Parent has unfinished prerequisite -> decomposed child must also be blocked!
        prereq = Task(owner_uid="alice", title="Prereq", duration_minutes=30, status="pending")
        parent = Task(owner_uid="alice", title="Parent", duration_minutes=60, status="pending")
        db.add_all([prereq, parent])
        db.flush()
        db.add(TaskDependency(owner_uid="alice", task_id=parent.id, depends_on_id=prereq.id))
        child = Task(owner_uid="alice", parent_task_id=parent.id, title="Child 1", duration_minutes=30, status="pending")
        db.add(child)
        db.flush()

        # Historical completed focus session never establishes task completion
        db.add(FocusSession(
            owner_uid="alice", task_id=prereq.id, status="completed",
            planned_seconds=1800, actual_seconds=1800,
            started_at=now - timedelta(hours=2), ended_at=now - timedelta(hours=1),
        ))

        # Future recurrence occurrence cannot start before occurrence_date
        series = RecurrenceSeries(
            owner_uid="alice", title="Daily Drill", duration_minutes=30, importance="important",
            frequency="daily", weekdays="", timezone="UTC", start_date=tomorrow, active=True,
        )
        db.add(series)
        db.flush()
        occ_task = Task(owner_uid="alice", title=f"Daily Drill ({tomorrow.isoformat()})", duration_minutes=30, status="pending")
        db.add(occ_task)
        db.flush()
        db.add(RecurrenceOccurrence(owner_uid="alice", series_id=series.id, occurrence_date=tomorrow, task_id=occ_task.id))
        db.commit()

        preview = get_preview(days=7, user={"uid": "alice"}, db=db)
        unsched_ids = {u["task_id"]: u["reason"] for u in preview["unscheduled"]}
        assert child.id in unsched_ids
        assert "Prerequisite" in unsched_ids[child.id]

        occ_blocks = [b for b in preview["blocks"] if b["task_id"] == occ_task.id]
        assert len(occ_blocks) == 1
        assert datetime.fromisoformat(occ_blocks[0]["starts_at"]).date() >= tomorrow


def test_worker_apply_entrypoints_and_cooldown(monkeypatch):
    engine = _setup_db()
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(Preference(owner_uid="alice", timezone="UTC", work_start=time(8), work_end=time(22)))
        db.flush()
        # Mixed missed + future tasks: t_missed had past block, t_future has future block
        t_missed = Task(owner_uid="alice", title="Missed Task", duration_minutes=30, status="pending")
        t_future = Task(owner_uid="alice", title="Future Task", duration_minutes=30, status="pending")
        db.add_all([t_missed, t_future])
        db.flush()
        db.add(ScheduleBlock(
            owner_uid="alice", task_id=t_missed.id,
            starts_at=now - timedelta(hours=4), ends_at=now - timedelta(hours=3),
        ))
        db.add(ScheduleBlock(
            owner_uid="alice", task_id=t_future.id,
            starts_at=now + timedelta(hours=4), ends_at=now + timedelta(hours=5),
        ))
        db.add(RecurrenceSeries(
            owner_uid="alice", title="Weekly Sync", duration_minutes=30, importance="important",
            frequency="daily", weekdays="", timezone="UTC", start_date=now.date(), active=True,
        ))
        db.commit()

    monkeypatch.setattr(expand_v2_recurrence, "engine", lambda: engine)
    monkeypatch.setattr(propose_v2_replans, "engine", lambda: engine)
    monkeypatch.setenv("CHRONOMIND_RECURRENCE_JOB_ENABLED", "1")
    monkeypatch.setenv("CHRONOMIND_REPLAN_JOB_ENABLED", "1")

    # Test expand_v2_recurrence --all-users --apply twice (deduplicates!)
    monkeypatch.setattr(sys, "argv", ["expand_v2_recurrence.py", "--all-users", "--days", "3", "--apply"])
    assert expand_v2_recurrence.main() == 0
    monkeypatch.setattr(sys, "argv", ["expand_v2_recurrence.py", "--all-users", "--days", "3", "--apply"])
    assert expand_v2_recurrence.main() == 0
    with Session(engine) as db:
        occs = db.scalars(select(RecurrenceOccurrence).where(RecurrenceOccurrence.owner_uid == "alice")).all()
        assert len(occs) == 3

    # Test propose_v2_replans --all-users --apply twice (creates 1 proposal, 2nd skipped by cooldown!)
    monkeypatch.setattr(sys, "argv", ["propose_v2_replans.py", "--all-users", "--apply"])
    assert propose_v2_replans.main() == 0
    monkeypatch.setattr(sys, "argv", ["propose_v2_replans.py", "--all-users", "--apply"])
    assert propose_v2_replans.main() == 0
    with Session(engine) as db:
        proposals = db.scalars(select(PlanProposal).where(PlanProposal.owner_uid == "alice")).all()
        notifs = db.scalars(select(InAppNotification).where(InAppNotification.owner_uid == "alice")).all()
        assert len(proposals) == 1
        assert len(notifs) == 1
