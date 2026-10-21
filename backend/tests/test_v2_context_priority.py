"""Focus-context tags and postponement history feed explainable priority scores."""
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.api import router as core_router
from v2.dashboard_api import router as dashboard_router
from v2.planning_api import router as planning_router
from v2.db import get_session
from v2.models import Base, Preference, ScheduleBlock, Task, User
from v2.priority import context_matches, score_task


def test_context_matching_is_deterministic_and_bounded():
    assert context_matches("Placement Season", ["placement prep"])
    assert context_matches("placement  season", ["Placement Season"])
    assert not context_matches(None, ["placement prep"])
    assert not context_matches("Placement", [])
    assert not context_matches("ab", ["ab"])  # too short to compare safely
    base = score_task("not_important", None, False, datetime(2026, 10, 14, tzinfo=timezone.utc))
    matched = score_task(
        "not_important", None, False, datetime(2026, 10, 14, tzinfo=timezone.utc),
        context_match=True,
    )
    assert matched.score == min(100, base.score + 15)
    assert "Matches your current focus context" in matched.reasons
    rigid = score_task(
        "not_important", None, False, datetime(2026, 10, 14, tzinfo=timezone.utc),
        splittable=False,
    )
    assert rigid.score == base.score + 5
    assert "Needs one continuous block (cannot be split)" in rigid.reasons


def make_app(engine):
    app = FastAPI()
    app.include_router(core_router)
    app.include_router(dashboard_router)
    app.include_router(planning_router)
    identity = {"uid": "alice"}
    app.dependency_overrides[get_current_user] = lambda: identity

    def session():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_session] = session
    return app, identity


def test_task_context_tags_roundtrip_and_scoring_explanation():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            db.add(User(uid="alice"))
            db.add(Preference(owner_uid="alice", focus_context="Placement Season"))
            db.commit()
        app, identity = make_app(engine)
        api = TestClient(app)

        # Tags are normalized server-side and returned to the owner.
        created = api.post("/api/v2/tasks", json={
            "title": "DSA practice", "duration_minutes": 45,
            "context_tags": ["  Placement Prep ", "placement prep", "interview"],
        })
        assert created.status_code == 201, created.text
        assert created.json()["context_tags"] == ["Placement Prep", "interview"]
        task_id = created.json()["id"]

        # Invalid tags are rejected with an explanatory 422.
        bad = api.post("/api/v2/tasks", json={
            "title": "Bad", "duration_minutes": 10, "context_tags": [""],
        })
        assert bad.status_code == 422
        too_many = api.post("/api/v2/tasks", json={
            "title": "Bad", "duration_minutes": 10,
            "context_tags": ["a1", "a2", "a3", "a4", "a5", "a6"],
        })
        assert too_many.status_code == 422

        # A past session on still-pending work records one postponement.
        with Session(engine) as db:
            db.add(ScheduleBlock(
                owner_uid="alice", task_id=task_id, source="manual",
                starts_at=datetime.now(timezone.utc) - timedelta(days=1),
                ends_at=datetime.now(timezone.utc) - timedelta(days=1, hours=-1),
            ))
            db.commit()

        dashboard = api.get("/api/v2/dashboard").json()
        entry = next(item for item in dashboard["top_priorities"] if item["id"] == task_id)
        assert entry["context_tags"] == ["Placement Prep", "interview"]
        assert entry["postponements"] == 1
        assert "Matches your current focus context" in entry["priority_reasons"]
        assert "Postponed 1 time(s)" in entry["priority_reasons"]
        assert dashboard["focus_context"] == "Placement Season"
        assert dashboard["scoring"]["context_match_bonus"] == 15

        # Preview scoring uses the same signals without committing anything.
        preview = api.get("/api/v2/planning/preview").json()
        assert preview["changes_committed"] is False
        assert preview["blocks"] or preview["unscheduled"]

        # A PATCH can update context tags with optimistic concurrency.
        patched = api.patch(f"/api/v2/tasks/{task_id}", json={
            "context_tags": ["interview"], "version": created.json()["version"],
        })
        assert patched.status_code == 200, patched.text
        assert patched.json()["context_tags"] == ["interview"]

        # Another tenant cannot see alice's tags through any listed payload.
        identity["uid"] = "bob"
        assert api.get("/api/v2/dashboard").json()["top_priorities"] == []
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
