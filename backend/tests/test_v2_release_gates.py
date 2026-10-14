"""Catch regressions that an isolated in-memory API build previously missed."""
from datetime import datetime, time, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.api import router as api_router
from v2.db import get_session
from v2.models import Base, ScheduleBlock, Task, User
from v2.planner import PlanningPreferences, PlanningTask, preview_schedule


def test_priority_engine_drives_scheduler_order():
    now = datetime(2026, 10, 15, 6, tzinfo=timezone.utc)
    opts = PlanningPreferences("Asia/Kolkata", time(8), time(20), 480, 10)
    low = PlanningTask("low", "Optional", 45, priority_score=10)
    urgent = PlanningTask("urgent", "Urgent", 45, priority_score=90)
    plan = preview_schedule([low, urgent], [], opts, now)
    assert plan.blocks[0].task_id == "urgent"


def test_task_crud_delete_is_safe_and_owned():
    engine = create_engine(
        "sqlite+pysqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            db.add_all([User(uid="alice"), User(uid="bob")])
            db.commit()
        app = FastAPI()
        app.include_router(api_router)
        user = {"uid": "alice"}
        app.dependency_overrides[get_current_user] = lambda: user
        def get_db():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[get_session] = get_db
        client = TestClient(app)
        first = client.post("/api/v2/tasks", json={"title":"Delete me"})
        assert first.status_code == 201, first.text
        task_id = first.json()["id"]
        user["uid"] = "bob"
        assert client.delete("/api/v2/tasks/" + task_id).status_code == 404
        user["uid"] = "alice"
        assert client.delete("/api/v2/tasks/" + task_id).status_code == 204
        assert client.get("/api/v2/tasks/" + task_id).status_code == 404
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_completed_task_clears_future_scheduled_blocks():
    engine = create_engine(
        "sqlite+pysqlite://", poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as db:
            db.add(User(uid="alice"))
            task = Task(owner_uid="alice", title="Finish", duration_minutes=60)
            db.add(task)
            db.flush()
            from datetime import timedelta
            future = datetime.now(timezone.utc) + timedelta(days=3)
            db.add(ScheduleBlock(
                owner_uid="alice", task_id=task.id,
                starts_at=future, ends_at=future + timedelta(minutes=60),
                source="plan:123e4567-e89b-12d3-a456-426614174000",
            ))
            db.commit()
            task_id = task.id
        app = FastAPI()
        app.include_router(api_router)
        app.dependency_overrides[get_current_user] = lambda: {"uid":"alice"}
        def get_db():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[get_session] = get_db
        client = TestClient(app)
        response = client.patch("/api/v2/tasks/" + task_id, json={
            "version":1, "status":"completed"
        })
        assert response.status_code == 200, response.text
        with Session(engine) as db:
            assert db.query(ScheduleBlock).count() == 0
        assert client.delete("/api/v2/tasks/" + task_id).status_code == 204
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
