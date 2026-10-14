"""Focus data are user-owned; behavioral recording requires explicit consent."""
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.db import get_session
from v2.focus_api import router
from v2.models import Base, BehaviorEvent, FocusSession, Task, User


def make_app():
    engine = create_engine(
        "sqlite+pysqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    app = FastAPI()
    app.include_router(router)
    user = {"uid": "alice"}
    app.dependency_overrides[get_current_user] = lambda: user

    def session_override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_session] = session_override
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(User(uid="bob"))
        db.add(Task(owner_uid="alice", title="Study", duration_minutes=30))
        db.commit()
        task_id = db.query(Task).filter_by(owner_uid="alice").one().id
    return engine, TestClient(app), user, task_id


def test_focus_consent_and_cross_user_security():
    engine, api, principal, task_id = make_app()
    try:
        assert api.get("/api/v2/focus/consent").json()["enabled"] is False
        response = api.post("/api/v2/focus/sessions", json={"task_id": task_id, "planned_minutes": 25})
        assert response.status_code == 201, response.text
        session_id = response.json()["id"]
        assert api.post("/api/v2/focus/sessions", json={"planned_minutes": 5}).status_code == 409
        with Session(engine) as db:
            row = db.get(FocusSession, session_id)
            row.started_at = datetime.now(timezone.utc) - timedelta(minutes=12)
            db.commit()
        principal["uid"] = "bob"
        assert api.get("/api/v2/focus/sessions").json() == []
        assert api.post("/api/v2/focus/sessions/" + session_id + "/finish", json={"outcome": "completed"}).status_code == 404
        assert api.post("/api/v2/focus/sessions", json={"task_id": task_id}).status_code == 404
        principal["uid"] = "alice"
        response = api.post("/api/v2/focus/sessions/" + session_id + "/finish", json={"outcome": "completed"})
        assert response.status_code == 200, response.text
        assert 11 * 60 <= response.json()["actual_seconds"] <= 13 * 60
        assert api.post("/api/v2/focus/sessions/" + session_id + "/finish", json={"outcome": "completed"}).status_code == 409
        assert api.get("/api/v2/focus/insights").json()["completed_sessions"] == 1
        with Session(engine) as db:
            assert db.query(BehaviorEvent).count() == 0
        assert api.put("/api/v2/focus/consent", json={"enabled": True}).status_code == 200
        new_session = api.post("/api/v2/focus/sessions", json={"planned_minutes": 10}).json()
        assert api.post("/api/v2/focus/sessions/" + new_session["id"] + "/finish", json={"outcome": "completed"}).status_code == 200
        with Session(engine) as db:
            assert db.query(BehaviorEvent).count() == 1
        result = api.put("/api/v2/focus/consent", json={"enabled": False})
        assert result.json()["past_behavior_removed"] is True
        with Session(engine) as db:
            assert db.query(BehaviorEvent).count() == 0
        assert api.get("/api/v2/focus/insights").json()["preferred_hour"] is None
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_rejects_bad_focus_duration():
    engine, api, _, _ = make_app()
    try:
        assert api.post("/api/v2/focus/sessions", json={"planned_minutes": 0}).status_code == 422
        assert api.post("/api/v2/focus/sessions", json={"planned_minutes": 241}).status_code == 422
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
