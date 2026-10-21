"""Proactive replan worker only targets genuinely missed or unplanned work."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from scripts.propose_v2_replans import inside_cooldown, needs_replan
from v2.models import Base, PlanProposal, ScheduleBlock, Task, User

NOW = datetime(2026, 10, 14, 8, 0, tzinfo=timezone.utc)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add(User(uid="alice"))
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_accounts_without_pending_work_are_skipped(db):
    assert needs_replan(db, "alice", NOW) == (False, "no pending tasks")


def test_overdue_deadline_triggers_replan(db):
    db.add(Task(
        owner_uid="alice", title="Late", duration_minutes=30,
        deadline_at=NOW - timedelta(days=1),
    ))
    db.commit()
    assert needs_replan(db, "alice", NOW) == (True, "overdue deadline")


def test_only_past_sessions_trigger_missed_recovery(db):
    task = Task(owner_uid="alice", title="Missed", duration_minutes=30)
    db.add(task)
    db.flush()
    db.add(ScheduleBlock(
        owner_uid="alice", task_id=task.id, source="manual",
        starts_at=NOW - timedelta(days=1), ends_at=NOW - timedelta(hours=23),
    ))
    db.commit()
    assert needs_replan(db, "alice", NOW) == (True, "all sessions for pending work are in the past")


def test_future_scheduled_work_is_left_alone(db):
    task = Task(owner_uid="alice", title="Booked", duration_minutes=30)
    db.add(task)
    db.flush()
    db.add(ScheduleBlock(
        owner_uid="alice", task_id=task.id, source="manual",
        starts_at=NOW + timedelta(hours=2), ends_at=NOW + timedelta(hours=3),
    ))
    db.commit()
    assert needs_replan(db, "alice", NOW) == (False, "current schedule still covers pending work")


def test_unplanned_pending_work_is_a_candidate(db):
    db.add(Task(owner_uid="alice", title="Never planned", duration_minutes=30))
    db.commit()
    assert needs_replan(db, "alice", NOW) == (True, "pending work has no scheduled sessions")


def test_recent_proposal_cooldown_prevents_spam(db):
    db.add(PlanProposal(
        owner_uid="alice", proposed_blocks=[], unscheduled=[],
        task_versions={}, preferences_snapshot={}, created_at=NOW,
    ))
    db.commit()
    assert inside_cooldown(db, "alice", NOW) is True
    assert inside_cooldown(db, "alice", NOW + timedelta(hours=13)) is False
    assert inside_cooldown(db, "bob", NOW) is False
