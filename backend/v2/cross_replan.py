"""Cross-feature event-move simulation and typed multi-record diff builder.

Simulates moving a fixed commitment (e.g. an exam), relocating conflicting
schedule blocks, and adding study sessions without mutating calendar rows.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import FixedEvent, Goal, Preference, ScheduleBlock, Task, TaskDependency
from .planner import BusyInterval, PlanningPreferences, PlanningTask
from .priority import context_matches, score_task
from .replanning import choose_schedule


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and (dt.tzinfo is None or dt.utcoffset() is None):
        return dt.replace(tzinfo=timezone.utc)
    return dt


def simulate_event_move_replan(
    db: Session,
    uid: str,
    event_id: str,
    new_starts_at: datetime,
    new_ends_at: datetime,
    *,
    horizon_days: int = 7,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Simulate moving a FixedEvent and reorganizing affected work in the horizon."""
    now = _aware(now_utc) or datetime.now(timezone.utc)
    new_start = _aware(new_starts_at).astimezone(timezone.utc)
    new_end = _aware(new_ends_at).astimezone(timezone.utc)
    if new_end <= new_start:
        raise HTTPException(422, "Event end must be after start")
    if new_start < now - timedelta(minutes=2):
        raise HTTPException(409, "Cannot move event into the past")

    target_event = db.scalar(select(FixedEvent).where(FixedEvent.owner_uid == uid, FixedEvent.id == event_id))
    if target_event is None:
        raise HTTPException(404, "Fixed event not found")

    pref = db.get(Preference, uid)
    opts = (
        PlanningPreferences("Asia/Kolkata", time(8), time(22), 480, 10)
        if pref is None
        else PlanningPreferences(
            pref.timezone, pref.work_start, pref.work_end,
            pref.max_daily_minutes, pref.min_break_minutes,
        )
    )
    zone = ZoneInfo(opts.timezone)

    old_start = _aware(target_event.starts_at).astimezone(timezone.utc)
    old_end = _aware(target_event.ends_at).astimezone(timezone.utc)

    other_events = db.scalars(
        select(FixedEvent).where(FixedEvent.owner_uid == uid, FixedEvent.id != event_id)
    ).all()
    all_blocks = db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid)).all()
    all_tasks = {
        t.id: t for t in db.scalars(select(Task).where(Task.owner_uid == uid)).all()
    }

    # Check if new event slot overlaps any unrelated protected fixed commitment
    for ev in other_events:
        ev_s, ev_e = _aware(ev.starts_at).astimezone(timezone.utc), _aware(ev.ends_at).astimezone(timezone.utc)
        if new_start < ev_e and new_end > ev_s:
            raise HTTPException(409, f"Moved event conflicts with protected commitment '{ev.title}'")

    # Identify schedule blocks that conflict with the moved event's new interval
    conflicting_blocks: list[ScheduleBlock] = []
    kept_blocks: list[ScheduleBlock] = []
    for blk in all_blocks:
        b_s = _aware(blk.starts_at).astimezone(timezone.utc)
        b_e = _aware(blk.ends_at).astimezone(timezone.utc)
        if b_s < new_end and b_e > new_start:
            conflicting_blocks.append(blk)
        else:
            kept_blocks.append(blk)

    # Build occupied intervals for post-move simulation (moved event + other fixed events + kept blocks)
    occupied: list[BusyInterval] = [BusyInterval(new_start, new_end, counts_as_work=False)]
    for ev in other_events:
        occupied.append(BusyInterval(_aware(ev.starts_at).astimezone(timezone.utc), _aware(ev.ends_at).astimezone(timezone.utc), counts_as_work=False))
    for blk in kept_blocks:
        occupied.append(BusyInterval(_aware(blk.starts_at).astimezone(timezone.utc), _aware(blk.ends_at).astimezone(timezone.utc), counts_as_work=True))

    operations: list[dict[str, Any]] = [
        {
            "op_type": "move_fixed_event",
            "entity_type": "fixed_event",
            "record_id": target_event.id,
            "title": target_event.title,
            "expected_version": target_event.version,
            "before": {"starts_at": old_start.isoformat(), "ends_at": old_end.isoformat()},
            "after": {"starts_at": new_start.isoformat(), "ends_at": new_end.isoformat()},
            "inverse": {
                "op_type": "move_fixed_event",
                "record_id": target_event.id,
                "starts_at": old_start.isoformat(),
                "ends_at": old_end.isoformat(),
            },
        }
    ]
    task_versions: dict[str, int] = {}
    unplaced: list[dict[str, Any]] = []

    # Relocate each conflicting block using the deterministic scheduler
    for blk in sorted(conflicting_blocks, key=lambda b: _aware(b.starts_at)):
        b_s = _aware(blk.starts_at).astimezone(timezone.utc)
        b_e = _aware(blk.ends_at).astimezone(timezone.utc)
        dur = max(1, int((b_e - b_s).total_seconds() // 60))
        task = all_tasks.get(blk.task_id)
        if task is None:
            unplaced.append({"task_id": blk.task_id, "title": "Unknown", "remaining_minutes": dur, "reason": "Task missing"})
            continue
        task_versions[task.id] = task.version
        pt = PlanningTask(
            task.id, task.title, dur, task.importance,
            _aware(task.deadline_at), None, 100, splittable=False,
        )
        reloc_plan, _ = choose_schedule([pt], occupied, opts, now, horizon_days)
        if not reloc_plan.blocks:
            unplaced.append({
                "task_id": task.id,
                "title": task.title,
                "remaining_minutes": dur,
                "reason": "Could not relocate displaced block within horizon",
            })
            continue
        moved_b = reloc_plan.blocks[0]
        m_s = moved_b.starts_at.astimezone(timezone.utc)
        m_e = moved_b.ends_at.astimezone(timezone.utc)
        occupied.append(BusyInterval(m_s, m_e, counts_as_work=True))
        operations.append({
            "op_type": "move_schedule_block",
            "entity_type": "schedule_block",
            "record_id": blk.id,
            "task_id": task.id,
            "title": task.title,
            "expected_version": blk.version,
            "before": {"starts_at": b_s.isoformat(), "ends_at": b_e.isoformat()},
            "after": {"starts_at": m_s.isoformat(), "ends_at": m_e.isoformat()},
            "inverse": {
                "op_type": "move_schedule_block",
                "record_id": blk.id,
                "starts_at": b_s.isoformat(),
                "ends_at": b_e.isoformat(),
            },
        })

    # Schedule remaining unscheduled pending leaf tasks (e.g. study sessions)
    container_ids = {t.parent_task_id for t in all_tasks.values() if t.parent_task_id is not None}
    deps = db.scalars(select(TaskDependency).where(TaskDependency.owner_uid == uid)).all()
    blockers = defaultdict(list)
    for d in deps:
        prereq = all_tasks.get(d.depends_on_id)
        if prereq is None or prereq.status != "completed":
            blockers[d.task_id].append(d.depends_on_id)
    for t in all_tasks.values():
        if t.parent_task_id and blockers.get(t.parent_task_id):
            for pid in blockers[t.parent_task_id]:
                if pid not in blockers[t.id]:
                    blockers[t.id].append(pid)

    future_scheduled = defaultdict(int)
    for blk in kept_blocks:
        b_s = _aware(blk.starts_at).astimezone(timezone.utc)
        b_e = _aware(blk.ends_at).astimezone(timezone.utc)
        if b_e > now:
            future_scheduled[blk.task_id] += int((b_e - max(b_s, now)).total_seconds() // 60)
    for op in operations:
        if op["op_type"] == "move_schedule_block":
            a_s = datetime.fromisoformat(op["after"]["starts_at"])
            a_e = datetime.fromisoformat(op["after"]["ends_at"])
            if a_e > now:
                future_scheduled[op["task_id"]] += int((a_e - max(a_s, now)).total_seconds() // 60)

    active_goals = {g.id for g in db.scalars(select(Goal).where(Goal.owner_uid == uid, Goal.status == "active")).all()}
    pending_leaves = [
        t for t in all_tasks.values()
        if t.status == "pending" and t.id not in container_ids
    ]
    planning_tasks = []
    for t in pending_leaves:
        rem = max(0, t.duration_minutes - future_scheduled[t.id])
        if rem <= 0:
            continue
        planning_tasks.append(PlanningTask(
            t.id, t.title, rem, t.importance, _aware(t.deadline_at),
            ("Prerequisite tasks are not yet completed: " + ", ".join(sorted(blockers[t.id])))
            if blockers[t.id] else None,
            score_task(
                t.importance, _aware(t.deadline_at), t.goal_id in active_goals, now,
                is_blocked=bool(blockers[t.id]), duration_minutes=t.duration_minutes,
                context_match=context_matches(pref.focus_context if pref else None, t.context_tags),
                splittable=t.splittable,
            ).score,
            t.splittable,
        ))

    added_plan, trace = choose_schedule(planning_tasks, occupied, opts, now, horizon_days)
    added_blocks = []
    for blk in added_plan.blocks:
        t = all_tasks[blk.task_id]
        task_versions[t.id] = t.version
        b_dict = {
            "task_id": blk.task_id,
            "title": blk.title,
            "starts_at": blk.starts_at.astimezone(timezone.utc).isoformat(),
            "ends_at": blk.ends_at.astimezone(timezone.utc).isoformat(),
            "duration_minutes": blk.duration_minutes,
        }
        added_blocks.append(b_dict)
        operations.append({
            "op_type": "add_schedule_block",
            "entity_type": "schedule_block",
            "record_id": None,
            "task_id": blk.task_id,
            "title": blk.title,
            "expected_version": t.version,
            "before": None,
            "after": b_dict,
            "inverse": {"op_type": "delete_schedule_block"},
        })

    for u in added_plan.unscheduled:
        unplaced.append({
            "task_id": u.task_id,
            "title": u.title,
            "remaining_minutes": u.remaining_minutes,
            "reason": u.reason,
        })

    comparison = {
        "baseline_fixed_event": {"id": target_event.id, "title": target_event.title, "starts_at": old_start.isoformat(), "ends_at": old_end.isoformat()},
        "proposed_fixed_event": {"id": target_event.id, "title": target_event.title, "starts_at": new_start.isoformat(), "ends_at": new_end.isoformat()},
        "relocated_blocks_count": sum(1 for o in operations if o["op_type"] == "move_schedule_block"),
        "added_blocks_count": len(added_blocks),
        "unplaced_count": len(unplaced),
        "timezone": opts.timezone,
    }
    return {
        "generated_at": now.isoformat(),
        "timezone": opts.timezone,
        "changes_committed": False,
        "operations": operations,
        "blocks": added_blocks,
        "unscheduled": unplaced,
        "task_versions": task_versions,
        "comparison": comparison,
        "decision_trace": {**trace, "mode": "cross_feature_replan"},
    }
