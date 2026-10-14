"""Read-only V2 planning API and tenant separation smoke tests."""
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.db import get_session
from v2.models import Base, FixedEvent, Task, User
from v2.planning_api import router


def test_preview_uses_stored_tasks_without_committing():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            db.add(User(uid="alice"))
            db.add(User(uid="bob"))
            db.flush()
            row = Task(owner_uid="alice", title="Long project", duration_minutes=60)
            db.add(row)
            db.commit()
            task_id = row.id

        app = FastAPI()
        app.include_router(router)
        principal = {"uid": "bob"}
        app.dependency_overrides[get_current_user] = lambda: principal

        def session():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_session] = session
        client = TestClient(app)
        assert client.get("/api/v2/planning/preview", params={"days": 0}).status_code == 422
        assert client.get("/api/v2/planning/preview").json()["blocks"] == []
        principal["uid"] = "alice"
        response = client.get("/api/v2/planning/preview")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["changes_committed"] is False
        assert any(block["task_id"] == task_id for block in data["blocks"])
        with Session(engine) as db:
            assert db.query(Task).filter(Task.owner_uid == "alice").count() == 1
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
