"""Stage 3 tests: two-tab stale edit rejection, decomposition preservation, goal versions, cancellation, and graph replay."""
from contextlib import contextmanager
from datetime import datetime, time, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2 import agent_api
from v2.agent_api import router as agent_router
from v2.agent_graph import build_planner_graph
from v2.api import router as v2_router
from v2.db import get_session
from v2.models import AgentRun, Base, Goal, PlanProposal, Preference, ScheduleBlock, Task, User
from v2.proposals_api import router as proposals_router


def _setup_db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


def _client(db: Session, uid: str = "alice"):
    app = FastAPI()
    app.include_router(v2_router)
    app.include_router(proposals_router)
    app.include_router(agent_router)
    app.dependency_overrides[get_current_user] = lambda: {"uid": uid}
    app.dependency_overrides[get_session] = lambda: db
    return TestClient(app)


def test_two_tabs_cannot_authorize_unseen_edit_and_cross_owner_fails():
    engine = _setup_db()
    with Session(engine) as db:
        db.add_all([User(uid="alice"), User(uid="bob")])
        db.add(Preference(owner_uid="alice", timezone="Asia/Kolkata", work_start=time(8), work_end=time(22)))
        db.flush()
        db.add(Task(owner_uid="alice", title="Study circuits", duration_minutes=30))
        db.commit()

        with _client(db, "alice") as alice_client:
            prop = alice_client.post("/api/v2/plans", json={"days": 3}).json()
            assert prop["revision"] == 1
            tab_a_rev = prop["revision"]
            tab_a_digest = prop["proposal_digest"]

            # Tab B moves the block by 1 hour -> revision increments to 2
            old_start = datetime.fromisoformat(prop["blocks"][0]["starts_at"])
            new_start = old_start + timedelta(hours=1)
            edited = alice_client.put(
                f"/api/v2/plans/{prop['id']}/blocks",
                json={"block_index": 0, "starts_at": new_start.isoformat()},
            )
            assert edited.status_code == 200
            assert edited.json()["revision"] == 2
            assert edited.json()["proposal_digest"] != tab_a_digest

            # Tab A tries to approve stale revision 1 -> 409!
            stale_approve = alice_client.post(
                f"/api/v2/plans/{prop['id']}/approve",
                json={"expected_revision": tab_a_rev, "proposal_digest": tab_a_digest},
            )
            assert stale_approve.status_code == 409

            # Cross-owner approval fails with 404
            with _client(db, "bob") as bob_client:
                cross = bob_client.post(f"/api/v2/plans/{prop['id']}/approve")
                assert cross.status_code == 404

            # Cancellation before commit prevents subsequent approval
            cancel = alice_client.post(f"/api/v2/plans/{prop['id']}/cancel")
            assert cancel.status_code == 200
            assert cancel.json()["status"] == "cancelled"
            after_cancel = alice_client.post(
                f"/api/v2/plans/{prop['id']}/approve",
                json={"expected_revision": 2, "proposal_digest": edited.json()["proposal_digest"]},
            )
            assert after_cancel.status_code == 409
            assert db.scalars(select(ScheduleBlock)).all() == []


def test_goal_version_check_and_decomposition_preserves_reviewed_payload():
    engine = _setup_db()
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.flush()
        task = Task(owner_uid="alice", title="Build project", duration_minutes=90)
        goal = Goal(owner_uid="alice", title="Graduate", description="Finish degree")
        db.add_all([task, goal])
        db.commit()

        with _client(db, "alice") as client:
            # Goal version check
            g_resp = client.patch(f"/api/v2/goals/{goal.id}", json={"title": "Graduate Honors", "version": 1})
            assert g_resp.status_code == 200
            assert g_resp.json()["version"] == 2
            g_stale = client.patch(f"/api/v2/goals/{goal.id}", json={"title": "Stale", "version": 1})
            assert g_stale.status_code == 409

            # Decomposition: preview then apply with exact reviewed titles and allocations
            reviewed = [
                {"title": "Custom Step A", "description": "First", "duration_minutes": 40},
                {"title": "Custom Step B", "description": "Second", "duration_minutes": 50},
            ]
            applied = client.post(
                f"/api/v2/tasks/{task.id}/decompose",
                json={"num_subtasks": 2, "apply": True, "subtasks": reviewed},
            )
            assert applied.status_code == 200
            subs = applied.json()["subtasks"]
            assert [(s["title"], s["duration_minutes"]) for s in subs] == [
                ("Custom Step A", 40),
                ("Custom Step B", 50),
            ]


def test_agent_run_lifecycle_and_cancel_with_in_memory_checkpointer(monkeypatch):
    engine = _setup_db()
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(Preference(owner_uid="alice", timezone="Asia/Kolkata", work_start=time(8), work_end=time(22)))
        db.flush()
        db.add(Task(owner_uid="alice", title="Control Systems", duration_minutes=30))
        db.commit()

    saver = MemorySaver()
    @contextmanager
    def fake_compiled_graph():
        yield build_planner_graph(agent_api.load_preview, agent_api.persist_proposal, saver)

    monkeypatch.setattr(agent_api, "engine", lambda: engine)
    monkeypatch.setattr(agent_api, "compiled_graph", fake_compiled_graph)

    with Session(engine) as db, _client(db, "alice") as client:
        # Idempotent run start by request_id
        r1 = client.post("/api/v2/agent/runs", json={"days": 3, "request_id": "req-abc"})
        r2 = client.post("/api/v2/agent/runs", json={"days": 3, "request_id": "req-abc"})
        assert r1.status_code == 201 and r2.status_code == 201
        assert r1.json()["run_id"] == r2.json()["run_id"]
        run_id = r1.json()["run_id"]

        runs = client.get("/api/v2/agent/runs").json()
        assert len(runs) == 1 and runs[0]["status"] == "awaiting_approval"

        # Cancel run before commit
        cancelled = client.post(f"/api/v2/agent/runs/{run_id}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"
        assert client.post(f"/api/v2/plans/{run_id}/approve").status_code == 409
