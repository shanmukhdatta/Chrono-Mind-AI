"""Test semantic task decomposition and subtask dependency creation."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.api import router
from v2.db import get_session
from v2.decomposition import decompose_task_logic
from v2.models import Base, Goal, Task, TaskDependency, User


@pytest.fixture
def client():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    app = FastAPI()
    app.include_router(router)
    identity = {"uid": "alice"}

    def fake_identity():
        return identity

    def testing_session():
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_current_user] = fake_identity
    app.dependency_overrides[get_session] = testing_session
    with TestClient(app) as browser:
        yield browser, identity, engine
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_deterministic_decomposition_logic():
    subtasks = decompose_task_logic("Build full-stack auth system", duration_minutes=90, num_subtasks=3)
    assert len(subtasks) == 3
    assert all("title" in s and "duration_minutes" in s for s in subtasks)
    total_duration = sum(s["duration_minutes"] for s in subtasks)
    assert total_duration == 90


def test_decompose_task_preview_does_not_mutate(client):
    api, identity, engine = client
    # Create parent task
    resp = api.post("/api/v2/tasks", json={"title": "Prepare ML Presentation", "duration_minutes": 90})
    assert resp.status_code == 201
    parent_id = resp.json()["id"]

    # Preview decomposition
    preview = api.post(f"/api/v2/tasks/{parent_id}/decompose", json={"num_subtasks": 3, "apply": False})
    assert preview.status_code == 200
    data = preview.json()
    assert data["applied"] is False
    assert len(data["subtasks"]) == 3
    assert len(data["dependencies"]) == 2

    # Verify no subtasks created in DB
    with Session(engine) as db:
        assert db.query(Task).count() == 1
        assert db.query(TaskDependency).count() == 0


def test_decompose_task_applied_creates_subtasks_and_dependencies(client):
    api, identity, engine = client
    # Create goal and parent task
    goal_resp = api.post("/api/v2/goals", json={"title": "Placement Season"})
    goal_id = goal_resp.json()["id"]

    resp = api.post("/api/v2/tasks", json={
        "title": "Build Final Year Project",
        "duration_minutes": 120,
        "goal_id": goal_id,
        "importance": "important",
    })
    parent_id = resp.json()["id"]

    # Apply decomposition
    applied = api.post(f"/api/v2/tasks/{parent_id}/decompose", json={"num_subtasks": 3, "apply": True})
    assert applied.status_code == 200
    data = applied.json()
    assert data["applied"] is True
    assert len(data["subtasks"]) == 3
    assert len(data["dependencies"]) == 2

    # Check list subtasks endpoint
    sub_resp = api.get(f"/api/v2/tasks/{parent_id}/subtasks")
    assert sub_resp.status_code == 200
    sub_items = sub_resp.json()
    assert len(sub_items) == 3
    assert all(item["parent_task_id"] == parent_id for item in sub_items)
    assert all(item["goal_id"] == goal_id for item in sub_items)

    # Check dependencies in DB
    step0_id = data["subtasks"][0]["id"]
    step1_id = data["subtasks"][1]["id"]
    step2_id = data["subtasks"][2]["id"]
    with Session(engine) as db:
        deps = db.query(TaskDependency).filter_by(owner_uid="alice").all()
        assert len(deps) == 2
        # Verify sequential link: step 1 depends on step 0, step 2 depends on step 1
        dep_pairs = {(d.task_id, d.depends_on_id) for d in deps}
        assert (step1_id, step0_id) in dep_pairs
        assert (step2_id, step1_id) in dep_pairs
