"""Only user-owned deadline notifications; duplicate jobs remain idempotent."""
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.db import get_session
from v2.models import Base, InAppNotification, Task, User
from v2.notifications_api import router, create_daily_notifications


def test_idempotent_deadline_generation_and_read_ownership():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    now = datetime(2026, 10, 14, 8, 0, tzinfo=timezone.utc)
    try:
        with Session(engine) as db:
            db.add_all([User(uid="alice"), User(uid="bob")])
            db.flush()
            db.add(Task(owner_uid="alice", title="Due soon", duration_minutes=30, deadline_at=now+timedelta(hours=4)))
            db.add(Task(owner_uid="alice", title="Already late", duration_minutes=30, deadline_at=now-timedelta(days=1)))
            db.add(Task(owner_uid="bob", title="Private", duration_minutes=30, deadline_at=now))
            db.commit()
            assert create_daily_notifications(db, "alice", now) == 2
            db.commit()
            assert create_daily_notifications(db, "alice", now) == 0
            db.commit()
            assert db.query(InAppNotification).filter_by(owner_uid="alice").count() == 2
            other_id = db.query(InAppNotification).filter_by(owner_uid="alice").first().id
        app = FastAPI()
        app.include_router(router)
        user = {"uid": "bob"}
        app.dependency_overrides[get_current_user] = lambda: user
        def override():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[get_session] = override
        api = TestClient(app)
        assert api.get("/api/v2/notifications").json() == []
        assert api.post("/api/v2/notifications/" + other_id + "/read").status_code == 404
        user["uid"] = "alice"
        assert api.get("/api/v2/notifications/unread-count").json()["unread_count"] == 2
        assert api.post("/api/v2/notifications/" + other_id + "/read").status_code == 200
        assert api.post("/api/v2/notifications/mark-all-read").json()["marked_read"] == 1
        assert api.get("/api/v2/notifications", params={"unread_only": "true"}).json() == []
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
