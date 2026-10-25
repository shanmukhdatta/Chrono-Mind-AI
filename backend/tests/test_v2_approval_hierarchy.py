"""Approvals must revalidate task-tree and prerequisite state at commit time."""
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from middleware.auth import get_current_user
from v2.db import get_session
from v2.api import router as tasks_router
from v2.proposals_api import router as plans_router
from v2.models import Base, User


def test_existing_proposal_cannot_schedule_new_parent_container():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.commit()
    app = FastAPI()
    app.include_router(tasks_router)
    app.include_router(plans_router)
    app.dependency_overrides[get_current_user] = lambda: {"uid": "alice"}
    def db_session():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_session] = db_session
    client = TestClient(app)
    try:
        parent = client.post("/api/v2/tasks", json={"title":"Essay", "duration_minutes":60})
        assert parent.status_code == 201, parent.text
        task = parent.json()
        proposal = client.post("/api/v2/plans", json={"days":7})
        assert proposal.status_code == 201, proposal.text
        plan_id = proposal.json()["id"]
        child = client.post("/api/v2/tasks", json={
            "title":"Outline", "duration_minutes":20, "parent_task_id":task["id"]
        })
        assert child.status_code == 201, child.text
        approved = client.post(f"/api/v2/plans/{plan_id}/approve")
        assert approved.status_code == 409, approved.text
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
