"""Approval integration tests against the SQLAlchemy V2 domain."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.db import get_session
from v2.models import Base, FixedEvent, ScheduleBlock, Task, User
from v2.proposals_api import router as plans
from v2.planning_api import router as preview


def make_test_app():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    app = FastAPI()
    app.include_router(plans)
    app.include_router(preview)
    identity = {"uid": "alice"}
    app.dependency_overrides[get_current_user] = lambda: identity

    def db_override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_session] = db_override
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(User(uid="bob"))
        db.add(Task(owner_uid="alice", title="Prepare", duration_minutes=40))
        db.commit()
    return engine, TestClient(app), identity


def test_propose_approve_undo_and_idempotency():
    engine, client, identity = make_test_app()
    try:
        proposal = client.post("/api/v2/plans", json={"days": 7})
        assert proposal.status_code == 201, proposal.text
        body = proposal.json()
        assert body["status"] == "pending"
        assert body["blocks"]
        with Session(engine) as db:
            assert db.query(ScheduleBlock).count() == 0
        identity["uid"] = "bob"
        assert client.get("/api/v2/plans/" + body["id"]).status_code == 404
        identity["uid"] = "alice"
        response = client.post("/api/v2/plans/" + body["id"] + "/approve")
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "approved"
        assert client.post("/api/v2/plans/" + body["id"] + "/approve").status_code == 409
        with Session(engine) as db:
            assert db.query(ScheduleBlock).count() == len(body["blocks"])
        response = client.post("/api/v2/plans/" + body["id"] + "/undo")
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "undone"
        with Session(engine) as db:
            assert db.query(ScheduleBlock).count() == 0
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_stale_task_is_rejected_without_calendar_writes():
    engine, client, _ = make_test_app()
    try:
        proposal = client.post("/api/v2/plans", json={"days": 7}).json()
        with Session(engine) as db:
            row = db.query(Task).filter(Task.owner_uid == "alice").one()
            row.version += 1
            db.commit()
        result = client.post("/api/v2/plans/" + proposal["id"] + "/approve")
        assert result.status_code == 409
        with Session(engine) as db:
            assert db.query(ScheduleBlock).count() == 0
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_rejected_proposal_cannot_be_applied():
    engine, client, _ = make_test_app()
    try:
        proposal = client.post("/api/v2/plans", json={"days": 7}).json()
        rejected = client.post("/api/v2/plans/" + proposal["id"] + "/reject")
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "rejected"
        assert client.post("/api/v2/plans/" + proposal["id"] + "/approve").status_code == 409
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
