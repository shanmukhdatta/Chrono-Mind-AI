"""Prerequisite graph rejects cycles, prevents cross-tenant edges, and gates plans."""
from datetime import datetime, time, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.db import get_session
from v2.dependencies_api import router, would_create_cycle
from v2.models import Base, Task, User
from v2.planner import PlanningPreferences, PlanningTask, preview_schedule


def test_cycle_check_transitive():
    assert would_create_cycle([("B", "C"), ("C", "A")], "A", "B")
    assert not would_create_cycle([("A", "B")], "C", "A")


def test_blocks_unsatisfied_prerequisite_without_discarding_task():
    options = PlanningPreferences("Asia/Kolkata", time(8), time(20), 480, 10)
    item = PlanningTask(
        "dependent", "Final report", 90, blocked_reason="Complete design first"
    )
    preview = preview_schedule(
        [item], [], options,
        datetime(2026, 10, 15, 7, tzinfo=timezone.utc),
    )
    assert not preview.blocks
    assert preview.unscheduled[0].remaining_minutes == 90
    assert preview.unscheduled[0].reason == "Complete design first"


def test_owner_only_dependency_crud_and_version_increment():
    engine = create_engine(
        "sqlite+pysqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            db.add_all([User(uid="alice"), User(uid="bob")])
            db.flush()
            rows = [
                Task(owner_uid="alice", title="A", duration_minutes=30),
                Task(owner_uid="alice", title="B", duration_minutes=30),
                Task(owner_uid="bob", title="Secret", duration_minutes=30),
            ]
            db.add_all(rows)
            db.commit()
            a,b,secret=(x.id for x in rows)
        app = FastAPI()
        app.include_router(router)
        user = {"uid":"alice"}
        app.dependency_overrides[get_current_user] = lambda: user
        def override():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[get_session] = override
        api = TestClient(app)
        assert api.post(f"/api/v2/tasks/{a}/dependencies", json={"depends_on_id": secret}).status_code == 404
        r = api.post(f"/api/v2/tasks/{a}/dependencies", json={"depends_on_id":b})
        assert r.status_code == 201, r.text
        assert api.post(f"/api/v2/tasks/{a}/dependencies", json={"depends_on_id":b}).json()["already_exists"]
        assert api.post(f"/api/v2/tasks/{b}/dependencies", json={"depends_on_id":a}).status_code == 409
        assert api.post(f"/api/v2/tasks/{a}/dependencies", json={"depends_on_id":a}).status_code == 422
        with Session(engine) as db:
            assert db.get(Task,a).version == 2
        assert api.get(f"/api/v2/tasks/{a}/dependencies").json()[0]["depends_on_id"] == b
        assert api.delete(f"/api/v2/tasks/{a}/dependencies/{b}").status_code == 204
        with Session(engine) as db:
            assert db.get(Task,a).version == 3
        user["uid"]="bob"
        assert api.get(f"/api/v2/tasks/{a}/dependencies").status_code == 404
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
