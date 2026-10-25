"""Regression coverage for safe task hierarchies and nonduplicating planning."""
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.api import router as task_router
from v2.dashboard_api import router as dashboard_router
from v2.planning_api import router as planning_router
from v2.db import get_session
from v2.models import Base, ScheduleBlock, Task, User


def test_owning_parent_and_no_double_scheduling(monkeypatch):
    # Force deterministic decomposition regardless of operator Groq configuration.
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    principal = {"uid": "alice"}
    with Session(engine) as db:
        db.add_all([User(uid="alice"), User(uid="bob")])
        db.commit()

    app = FastAPI()
    for router in (task_router, dashboard_router, planning_router):
        app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: principal
    def session():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_session] = session
    client = TestClient(app)

    try:
        parent = client.post("/api/v2/tasks", json={"title": "Research poster", "duration_minutes": 90}).json()
        parent_id = parent["id"]
        principal["uid"] = "bob"
        assert client.post("/api/v2/tasks", json={
            "title": "Cross-account child", "duration_minutes": 30, "parent_task_id": parent_id,
        }).status_code == 404
        principal["uid"] = "alice"
        child = client.post("/api/v2/tasks", json={
            "title": "Outline", "duration_minutes": 30, "parent_task_id": parent_id
        }).json()
        assert client.patch("/api/v2/tasks/" + parent_id, json={
            "version": parent["version"], "parent_task_id": child["id"]
        }).status_code == 409
        assert client.delete("/api/v2/tasks/" + parent_id).status_code == 409
        assert client.post("/api/v2/tasks/" + parent_id + "/decompose", json={
            "apply": True
        }).status_code == 409
        preview = client.get("/api/v2/planning/preview?days=7").json()
        listed_ids = {b["task_id"] for b in preview["blocks"]} | {t["task_id"] for t in preview["unscheduled"]}
        assert parent_id not in listed_ids
        assert child["id"] in listed_ids
        top_ids = {item["id"] for item in client.get("/api/v2/dashboard").json()["top_priorities"]}
        assert parent_id not in top_ids
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_decomposition_preserves_exact_total_and_draft(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    app = FastAPI()
    app.include_router(task_router)
    app.dependency_overrides[get_current_user] = lambda: {"uid": "alice"}
    def session():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_session] = session
    client = TestClient(app)
    try:
        task_id = client.post("/api/v2/tasks", json={
            "title": "Analyze experiments", "duration_minutes": 95
        }).json()["id"]
        drafts = [
            {"title": "Prepare data", "duration_minutes": 30},
            {"title": "Analyze", "duration_minutes": 45},
            {"title": "Summarize", "duration_minutes": 20},
        ]
        bad = client.post(f"/api/v2/tasks/{task_id}/decompose", json={
            "apply": True, "subtasks": [{**drafts[0], "duration_minutes": 25}, *drafts[1:]]
        })
        assert bad.status_code == 422
        good = client.post(f"/api/v2/tasks/{task_id}/decompose", json={
            "apply": True, "subtasks": drafts
        })
        assert good.status_code == 200, good.text
        assert [t["title"] for t in good.json()["subtasks"]] == [t["title"] for t in drafts]
        assert sum(t["duration_minutes"] for t in good.json()["subtasks"]) == 95
        assert client.post(f"/api/v2/tasks/{task_id}/decompose", json={
            "apply": True
        }).status_code == 409
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
