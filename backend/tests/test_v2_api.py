"""Isolated PostgreSQL-domain API tests with SQLite in-memory."""
import os
os.environ["CHRONOMIND_DISABLE_LEGACY_SCHEDULER"] = "1"

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.api import router
from v2.db import get_session
from v2.models import Base


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
        yield browser, identity
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_goals_and_task_ownership(client):
    api, identity = client
    response = api.post("/api/v2/goals", json={"title": "Learn Python"})
    assert response.status_code == 201, response.text
    goal = response.json()
    response = api.post("/api/v2/tasks", json={"title": "Functions", "goal_id": goal["id"], "duration_minutes": 45})
    assert response.status_code == 201, response.text
    task = response.json()
    assert len(api.get("/api/v2/tasks").json()) == 1
    identity["uid"] = "bob"
    assert api.get("/api/v2/tasks").json() == []
    assert api.get("/api/v2/goals").json() == []
    assert api.get("/api/v2/tasks/" + task["id"]).status_code == 404
    assert api.patch("/api/v2/tasks/" + task["id"], json={"version": 1, "title": "Stolen"}).status_code == 404
    assert api.post("/api/v2/tasks", json={"title": "Wrong goal", "goal_id": goal["id"]}).status_code == 404
    identity["uid"] = "alice"
    assert api.get("/api/v2/tasks/" + task["id"]).json()["title"] == "Functions"


def test_optimistic_locking_and_completion(client):
    api, _ = client
    row = api.post("/api/v2/tasks", json={"title": "Study"}).json()
    url = "/api/v2/tasks/" + row["id"]
    updated = api.patch(url, json={"version": 1, "status": "completed"})
    assert updated.status_code == 200, updated.text
    assert updated.json()["version"] == 2
    assert api.patch(url, json={"version": 1, "title": "Stale"}).status_code == 409
    assert api.get(url).json()["status"] == "completed"


def test_goals_deletion_preserves_tasks(client):
    api, _ = client
    goal = api.post("/api/v2/goals", json={"title": "Career"}).json()
    task = api.post("/api/v2/tasks", json={"title": "Portfolio", "goal_id": goal["id"]}).json()
    assert api.delete("/api/v2/goals/" + goal["id"]).status_code == 204
    assert api.get("/api/v2/tasks/" + task["id"]).json()["goal_id"] is None


def test_preferences_and_validation(client):
    api, _ = client
    assert api.get("/api/v2/preferences").json()["timezone"] == "Asia/Kolkata"
    assert api.put("/api/v2/preferences", json={"timezone": "Mars/Phobos"}).status_code == 422
    valid = api.put("/api/v2/preferences", json={"timezone": "Europe/London", "max_daily_minutes": 240})
    assert valid.status_code == 200
    assert valid.json()["timezone"] == "Europe/London"
    assert api.post("/api/v2/tasks", json={"title": "x", "deadline_at": "2026-10-15T12:00:00"}).status_code == 422
    assert api.post("/api/v2/goals", json={"title": "  "}).status_code == 422
