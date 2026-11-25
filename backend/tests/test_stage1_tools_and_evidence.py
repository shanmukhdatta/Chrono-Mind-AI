"""Stage 1 tests: owner-bound tools, exact counts/pagination, evidence, disambiguation, and calendar coverage."""
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.assistant import router as assistant_router
from v2.db import get_session
from v2.models import Base, BehaviorConsent, BehaviorEvent, FixedEvent, Preference, Task, User
from v2.tools import (
    count_tasks,
    get_calendar_range,
    get_consented_focus_summary,
    list_tasks,
    resolve_local_date,
    resolve_target_entity,
)


def _setup_db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


def test_47_pending_tasks_exact_count_and_pagination_via_chat():
    engine = _setup_db()
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.flush()
        for i in range(47):
            db.add(Task(owner_uid="alice", title=f"Task {i:02d}", duration_minutes=30))
        db.add(User(uid="bob"))
        db.flush()
        db.add(Task(owner_uid="bob", title="Task 00", duration_minutes=30))
        db.commit()

        assert count_tasks(db, "alice")["count"] == 47
        p1 = list_tasks(db, "alice", limit=20, offset=0)
        p2 = list_tasks(db, "alice", limit=20, offset=20)
        p3 = list_tasks(db, "alice", limit=20, offset=40)
        assert p1["pagination"]["total"] == 47
        assert len(p1["items"]) == 20 and p1["pagination"]["has_more"] is True
        assert len(p2["items"]) == 20 and p2["pagination"]["has_more"] is True
        assert len(p3["items"]) == 7 and p3["pagination"]["has_more"] is False
        assert p1["complete"] is False

        app = FastAPI()
        app.include_router(assistant_router)
        app.dependency_overrides[get_current_user] = lambda: {"uid": "alice"}
        app.dependency_overrides[get_session] = lambda: db

        with TestClient(app) as client:
            r_count = client.post("/api/v2/assistant/chat", json={"message": "How many pending tasks do I have?"})
            assert r_count.status_code == 200
            assert "47 pending tasks" in r_count.json()["decision"]["message"]
            assert r_count.json()["evidence"][0]["fields"]["count"] == 47

            r_list = client.post("/api/v2/assistant/chat", json={"message": "List my pending tasks", "limit": 20, "offset": 40})
            assert r_list.status_code == 200
            body = r_list.json()
            assert body["pagination"]["total"] == 47
            assert body["pagination"]["returned"] == 7
            assert "47 pending tasks" in body["decision"]["message"]


def test_cross_owner_isolation_and_exam_vs_task_disambiguation():
    engine = _setup_db()
    now = datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc)
    with Session(engine) as db:
        db.add_all([User(uid="alice"), User(uid="bob")])
        db.flush()
        alice_task = Task(owner_uid="alice", title="Control Systems revision", duration_minutes=45)
        alice_exam = FixedEvent(
            owner_uid="alice",
            title="Control Systems exam",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=2),
        )
        bob_task = Task(owner_uid="bob", title="Control Systems secret", duration_minutes=30)
        db.add_all([alice_task, alice_exam, bob_task])
        db.commit()

        # Never returns bob's record
        res_task = resolve_target_entity(db, "alice", "Control Systems revision", expected_type="task", now_utc=now)
        assert res_task["status"] == "resolved"
        assert res_task["entity"]["id"] == alice_task.id
        assert res_task["entity"]["entity_type"] == "task"

        res_exam = resolve_target_entity(db, "alice", "Control Systems exam", expected_type="fixed_event", now_utc=now)
        assert res_exam["status"] == "resolved"
        assert res_exam["entity"]["id"] == alice_exam.id
        assert res_exam["entity"]["entity_type"] == "fixed_event"

        # Duplicate same-title tasks trigger targeted question unless selected_id disambiguates
        dup1 = Task(owner_uid="alice", title="Lab report", duration_minutes=30)
        dup2 = Task(owner_uid="alice", title="Lab report", duration_minutes=60)
        db.add_all([dup1, dup2])
        db.commit()

        ambig = resolve_target_entity(db, "alice", "Lab report", expected_type="task", now_utc=now)
        assert ambig["status"] == "ambiguous"
        assert "Lab report" in ambig["question"]

        selected = resolve_target_entity(
            db, "alice", "Lab report", expected_type="task", selected_id=dup2.id, selected_type="task", now_utc=now
        )
        assert selected["status"] == "resolved"
        assert selected["entity"]["id"] == dup2.id


def test_partial_calendar_coverage_and_local_dates_and_focus_consent():
    engine = _setup_db()
    now = datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc)  # 23:30 IST on 2026-11-24
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(Preference(owner_uid="alice", timezone="Asia/Kolkata"))
        db.flush()
        for i in range(4):
            db.add(FixedEvent(
                owner_uid="alice",
                title=f"Class {i}",
                starts_at=now + timedelta(hours=i + 1),
                ends_at=now + timedelta(hours=i + 2),
            ))
        db.commit()

        # Local date in Asia/Kolkata at 18:00 UTC is 2026-11-24, tomorrow is 2026-11-25
        assert resolve_local_date("tomorrow", "Asia/Kolkata", now).isoformat() == "2026-11-25"

        # Truncated calendar query marks complete=False
        partial = get_calendar_range(db, "alice", now, now + timedelta(days=1), limit=2, now_utc=now)
        assert partial["complete"] is False
        assert partial["truncated"] is True

        full = get_calendar_range(db, "alice", now, now + timedelta(days=1), limit=20, now_utc=now)
        assert full["complete"] is True
        assert len(full["fixed_events"]) == 4

        # Focus consent off -> no inferred preference leaked
        unconsented = get_consented_focus_summary(db, "alice", now_utc=now)
        assert unconsented["consented"] is False
        assert unconsented["summary"]["preferred_hour"] is None

        db.add(BehaviorConsent(owner_uid="alice", enabled=True))
        for _ in range(5):
            db.add(BehaviorEvent(owner_uid="alice", kind="focus_completed", hour_of_day=19, duration_seconds=1800))
        db.commit()
        consented = get_consented_focus_summary(db, "alice", now_utc=now)
        assert consented["consented"] is True
        assert consented["summary"]["preferred_hour"] == 19
        assert consented["summary"]["sample_size"] == 5
