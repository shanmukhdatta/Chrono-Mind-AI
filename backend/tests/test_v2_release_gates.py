"""Release-gate regressions for actual browser preflights and missed sessions."""
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from main import app
from middleware.auth import get_current_user
from v2.db import get_session
from v2.models import Base, ScheduleBlock, Task, User
from v2.planning_api import router as preview_router


def test_v2_mutating_cors_methods_are_preflight_authorized():
    with TestClient(app) as client:
        for method, target in (
            ("PUT", "/api/v2/preferences"),
            ("PUT", "/api/v2/fixed-events/example"),
            ("POST", "/api/v2/tasks"),
            ("PATCH", "/api/v2/tasks/example"),
            ("DELETE", "/api/v2/fixed-events/example"),
        ):
            response = client.options(target, headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "authorization,content-type",
            })
            assert response.status_code == 200, (method, response.text)
            allowed = response.headers["access-control-allow-methods"].split(", ")
            assert method in allowed


def test_readiness_is_not_falsely_green_without_database(monkeypatch):
    from v2.db import engine
    engine.cache_clear()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        response = client.get("/health/v2")
        assert response.status_code == 503
        assert response.json()["detail"] == "V2 PostgreSQL is not ready"
    engine.cache_clear()


def test_missed_sessions_are_eligible_for_new_proposals():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        now = datetime.now(timezone.utc)
        with Session(engine) as db:
            db.add(User(uid="alice"))
            db.flush()
            task = Task(owner_uid="alice", title="Missed but not completed", duration_minutes=60)
            db.add(task)
            db.flush()
            db.add(ScheduleBlock(
                owner_uid="alice", task_id=task.id,
                starts_at=now - timedelta(days=2, hours=1),
                ends_at=now - timedelta(days=2), source="manual",
            ))
            db.commit()
            task_id = task.id
        preview_app = FastAPI()
        preview_app.include_router(preview_router)
        preview_app.dependency_overrides[get_current_user] = lambda: {"uid": "alice"}
        def testing_db():
            with Session(engine) as db:
                yield db
        preview_app.dependency_overrides[get_session] = testing_db
        response = TestClient(preview_app).get("/api/v2/planning/preview")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["changes_committed"] is False
        assert sum(block["duration_minutes"] for block in body["blocks"] if block["task_id"] == task_id) == 60
        with Session(engine) as db:
            assert db.query(ScheduleBlock).count() == 1, "Preview must not write"
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
