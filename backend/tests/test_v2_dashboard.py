from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.db import get_session
from v2.models import Base, Goal, Task, User
from v2.dashboard_api import router
from v2.priority import score_task


def test_priority_is_explainable_and_monotonic():
    now = datetime(2026, 10, 14, tzinfo=timezone.utc)
    baseline = score_task("not_important", None, False, now)
    important = score_task("important", None, False, now)
    urgent = score_task("important", now + timedelta(hours=4), True, now)
    overdue = score_task("important", now - timedelta(days=1), True, now)
    assert baseline.score == 15
    assert baseline.score < important.score < urgent.score <= overdue.score
    assert "Deadline passed" in overdue.reasons


def test_dashboard_counts_and_cross_user_filtering():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            db.add(User(uid="alice"))
            db.add(User(uid="bob"))
            db.add(Task(owner_uid="alice", title="One", status="pending", duration_minutes=50))
            db.add(Task(owner_uid="alice", title="Two", status="completed", duration_minutes=20))
            db.add(Task(owner_uid="bob", title="Secret", duration_minutes=20))
            db.commit()
        app = FastAPI()
        app.include_router(router)
        principal = {"uid": "alice"}
        app.dependency_overrides[get_current_user] = lambda: principal
        def session():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[get_session] = session
        api = TestClient(app)
        response = api.get("/api/v2/dashboard")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["pending_count"] == 1
        assert body["completed_count"] == 1
        assert body["completion_rate"] == 50.0
        assert body["top_priorities"][0]["title"] == "One"
        assert len(body["completed_last_seven_days"]) == 7
        principal["uid"] = "bob"
        assert api.get("/api/v2/dashboard").json()["top_priorities"][0]["title"] == "Secret"
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
