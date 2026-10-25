"""Test adaptive replanning triggers, account cross-store deletion, and monthly recurrence."""
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.api import router as v2_core_router
from v2.account_data import router as v2_account_router
from v2.planning_api import router as v2_planning_router
from v2.recurrence import router as v2_recurrence_router
from v2.db import get_session
from v2.models import (
    Base, Goal, InAppNotification, PlanProposal, PlanningDecisionLog,
    Preference, RecurrenceSeries, Task, User
)


@pytest.fixture
def test_setup():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    app = FastAPI()
    app.include_router(v2_core_router)
    app.include_router(v2_account_router)
    app.include_router(v2_planning_router)
    app.include_router(v2_recurrence_router)
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


def test_trigger_adaptive_replan_creates_proposal_and_notification(test_setup):
    api, identity, engine = test_setup
    now = datetime.now(timezone.utc)

    # Create task needing schedule
    t_resp = api.post("/api/v2/tasks", json={
        "title": "Study for Midterm", "duration_minutes": 60, "importance": "important",
        "deadline_at": (now + timedelta(days=2)).isoformat(),
    })
    assert t_resp.status_code == 201

    # Trigger adaptive replan
    replan_resp = api.post("/api/v2/planning/replan", json={
        "days": 7, "trigger": "missed_tasks", "notify": True
    })
    assert replan_resp.status_code == 200
    data = replan_resp.json()
    assert data["proposal_id"] is not None
    assert data["notification_sent"] is True
    assert data["trigger"] == "missed_tasks"

    with Session(engine) as db:
        # Check proposal saved
        prop = db.get(PlanProposal, data["proposal_id"])
        assert prop is not None
        assert prop.owner_uid == "alice"
        assert prop.status == "pending"

        # Check decision log recorded
        log = db.query(PlanningDecisionLog).filter_by(proposal_id=prop.id).first()
        assert log is not None
        assert log.action == "replanned"
        assert "ADAPTIVE_REPLAN" in log.reason_codes

        # Check notification created
        notif = db.query(InAppNotification).filter_by(owner_uid="alice").first()
        assert notif is not None
        assert notif.kind == "replan_available"
        assert "missed tasks" in notif.message


def test_account_deletion_purges_all_user_records(test_setup):
    api, identity, engine = test_setup
    now = datetime.now(timezone.utc)

    # Seed Alice data
    api.post("/api/v2/goals", json={"title": "Goal to be deleted"})
    api.post("/api/v2/tasks", json={"title": "Task to be deleted", "duration_minutes": 30})

    # Seed Bob data (should remain untouched)
    identity["uid"] = "bob"
    api.post("/api/v2/goals", json={"title": "Bob Goal"})
    api.post("/api/v2/tasks", json={"title": "Bob Task", "duration_minutes": 45})

    # Switch back to Alice and delete account data
    identity["uid"] = "alice"
    del_resp = api.delete("/api/v2/account")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is False  # Firebase identity remains; no false claim of full erasure
    assert del_resp.json()["status"] == "partial"
    assert del_resp.json()["postgres_deleted"] is True
    assert del_resp.json()["firebase_auth_deleted"] is False
    assert del_resp.json()["uid"] == "alice"

    # Verify Alice data is completely wiped while Bob data remains
    with Session(engine) as db:
        assert db.query(Goal).filter_by(owner_uid="alice").count() == 0
        assert db.query(Task).filter_by(owner_uid="alice").count() == 0
        assert db.query(User).filter_by(uid="alice").count() == 0

        # Bob remains intact
        assert db.query(Goal).filter_by(owner_uid="bob").count() == 1
        assert db.query(Task).filter_by(owner_uid="bob").count() == 1
        assert db.query(User).filter_by(uid="bob").count() == 1


def test_monthly_recurrence_series_and_materialization(test_setup):
    api, identity, engine = test_setup
    today = date.today()

    # Create monthly series
    resp = api.post("/api/v2/recurrence", json={
        "title": "Monthly Rent & Utility Review",
        "duration_minutes": 45,
        "importance": "important",
        "frequency": "monthly",
        "start_date": today.isoformat(),
        "timezone": "Asia/Kolkata",
    })
    assert resp.status_code == 201
    series_id = resp.json()["id"]
    assert resp.json()["frequency"] == "monthly"

    # Materialize occurrences for next 60 days
    mat_resp = api.post(f"/api/v2/recurrence/{series_id}/materialize?days=60")
    assert mat_resp.status_code == 200
    mat_data = mat_resp.json()
    assert mat_data["created"] >= 1

    # Verify idempotency (second call creates 0)
    second_mat = api.post(f"/api/v2/recurrence/{series_id}/materialize?days=60")
    assert second_mat.status_code == 200
    assert second_mat.json()["created"] == 0
