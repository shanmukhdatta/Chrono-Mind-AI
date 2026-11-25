"""Stage 2 tests: complete one-task scheduling loop, idempotency, receipts, and read-back recovery."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2 import proposals_api
from v2.assistant import router as assistant_router
from v2.db import get_session
from v2.models import Base, FixedEvent, OperationReceipt, Preference, ScheduleBlock, Task, TaskDependency, User
from v2.planning_api import router as planning_router
from v2.proposals_api import router as proposals_router


def _build_client(db: Session, uid: str = "alice"):
    app = FastAPI()
    app.include_router(assistant_router)
    app.include_router(planning_router)
    app.include_router(proposals_router)
    app.dependency_overrides[get_current_user] = lambda: {"uid": uid}
    app.dependency_overrides[get_session] = lambda: db
    return TestClient(app)


def _setup_db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


def test_one_task_loop_approve_idempotent_and_reject():
    engine = _setup_db()
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(Preference(owner_uid="alice", timezone="Asia/Kolkata", work_start=time(8), work_end=time(22)))
        db.flush()
        task = Task(owner_uid="alice", title="Control Systems revision", duration_minutes=60, splittable=True)
        db.add(task)
        db.commit()

        with _build_client(db) as client:
            # Repeated start with same idempotency_key returns same proposal
            r1 = client.post(
                "/api/v2/assistant/chat",
                json={
                    "message": "Find 30 minutes tomorrow for my existing Control Systems revision task",
                    "idempotency_key": "start-1",
                },
            )
            r2 = client.post(
                "/api/v2/assistant/chat",
                json={
                    "message": "Find 30 minutes tomorrow for my existing Control Systems revision task",
                    "idempotency_key": "start-1",
                },
            )
            assert r1.status_code == 200
            d1 = r1.json()["decision"]
            d2 = r2.json()["decision"]
            assert d1["kind"] == "draft_schedule_proposal"
            draft = d1["draft_schedule_proposal"]
            assert draft["proposal_id"] == d2["draft_schedule_proposal"]["proposal_id"]
            assert len(draft["blocks"]) == 1
            assert draft["blocks"][0]["duration_minutes"] == 30
            assert draft["blocks"][0]["task_id"] == task.id

            # Before approval, zero schedule blocks exist
            assert db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == "alice")).all() == []

            # Approve twice with same idempotency_key -> exactly 1 block created
            a1 = client.post(
                f"/api/v2/plans/{draft['proposal_id']}/approve",
                json={
                    "expected_revision": draft["revision"],
                    "proposal_digest": draft["proposal_digest"],
                    "idempotency_key": "approve-1",
                },
            )
            a2 = client.post(
                f"/api/v2/plans/{draft['proposal_id']}/approve",
                json={
                    "expected_revision": draft["revision"],
                    "proposal_digest": draft["proposal_digest"],
                    "idempotency_key": "approve-1",
                },
            )
            assert a1.status_code == 200 and a2.status_code == 200
            assert a1.json()["verification_status"] == "verified"
            assert a1.json()["calendar_link"] == "/app/v2/calendar"
            assert a1.json()["receipt_id"] == a2.json()["receipt_id"]
            blocks = db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == "alice")).all()
            assert len(blocks) == 1
            assert blocks[0].task_id == task.id

            # Rejection path creates zero blocks
            r_rej = client.post(
                "/api/v2/assistant/chat",
                json={"message": "Find 30 minutes tomorrow for my existing Control Systems revision task"},
            )
            rej_id = r_rej.json()["decision"]["draft_schedule_proposal"]["proposal_id"]
            rej = client.post(f"/api/v2/plans/{rej_id}/reject")
            assert rej.status_code == 200
            assert rej.json()["status"] == "rejected"
            assert len(db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == "alice")).all()) == 1


def test_newly_occupied_slot_conflicts_and_readback_outage_retries_verification_only(monkeypatch):
    engine = _setup_db()
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(Preference(owner_uid="alice", timezone="Asia/Kolkata", work_start=time(8), work_end=time(22)))
        db.flush()
        t1 = Task(owner_uid="alice", title="Control Systems revision", duration_minutes=60)
        t2 = Task(owner_uid="alice", title="Signals practice", duration_minutes=30)
        db.add_all([t1, t2])
        db.commit()

        with _build_client(db) as client:
            # 1. Conflict case: occupy the proposed slot before approval
            r = client.post(
                "/api/v2/assistant/chat",
                json={"message": "Find 30 minutes tomorrow for my existing Control Systems revision task"},
            )
            draft = r.json()["decision"]["draft_schedule_proposal"]
            blk = draft["blocks"][0]
            db.add(FixedEvent(
                owner_uid="alice",
                title="Surprise meeting",
                starts_at=datetime.fromisoformat(blk["starts_at"]),
                ends_at=datetime.fromisoformat(blk["ends_at"]),
            ))
            db.commit()
            conflict_resp = client.post(
                f"/api/v2/plans/{draft['proposal_id']}/approve",
                json={"expected_revision": draft["revision"], "proposal_digest": draft["proposal_digest"]},
            )
            assert conflict_resp.status_code == 409

            # 2. Read-back outage retries verification only without duplicating
            r2 = client.post(
                "/api/v2/assistant/chat",
                json={"message": "Find 30 minutes tomorrow for my existing Signals practice task"},
            )
            draft2 = r2.json()["decision"]["draft_schedule_proposal"]

            real_verify = proposals_api.verify_committed_records
            def failing_verify(*args, **kwargs):
                raise RuntimeError("Simulated read-back outage")

            monkeypatch.setattr(proposals_api, "verify_committed_records", failing_verify)
            outage_resp = client.post(
                f"/api/v2/plans/{draft2['proposal_id']}/approve",
                json={
                    "expected_revision": draft2["revision"],
                    "proposal_digest": draft2["proposal_digest"],
                    "idempotency_key": "approve-outage",
                },
            )
            assert outage_resp.status_code == 200
            assert outage_resp.json()["verification_status"] == "committed_unverified"
            assert len(db.scalars(select(ScheduleBlock).where(ScheduleBlock.task_id == t2.id)).all()) == 1

            # Restore read-back and retry verification only
            monkeypatch.setattr(proposals_api, "verify_committed_records", real_verify)
            retry_resp = client.post(f"/api/v2/plans/{draft2['proposal_id']}/verify")
            assert retry_resp.status_code == 200
            assert retry_resp.json()["verification_status"] == "verified"
            assert len(db.scalars(select(ScheduleBlock).where(ScheduleBlock.task_id == t2.id)).all()) == 1


def test_indivisible_and_blocked_task_reasons():
    engine = _setup_db()
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.flush()
        prereq = Task(owner_uid="alice", title="Read notes", duration_minutes=30, status="pending")
        blocked = Task(owner_uid="alice", title="Lab assignment", duration_minutes=60, status="pending")
        indivis = Task(owner_uid="alice", title="Mock exam", duration_minutes=60, splittable=False, status="pending")
        db.add_all([prereq, blocked, indivis])
        db.flush()
        db.add(TaskDependency(owner_uid="alice", task_id=blocked.id, depends_on_id=prereq.id))
        db.commit()

        with _build_client(db) as client:
            r_blk = client.post(
                "/api/v2/assistant/chat",
                json={"message": "Find 30 minutes tomorrow for my existing Lab assignment task"},
            )
            assert r_blk.json()["decision"]["kind"] == "answer"
            assert "prerequisite" in r_blk.json()["decision"]["message"].lower()

            r_ind = client.post(
                "/api/v2/assistant/chat",
                json={"message": "Find 30 minutes tomorrow for my existing Mock exam task"},
            )
            assert r_ind.json()["decision"]["kind"] == "answer"
            assert "indivisible" in r_ind.json()["decision"]["message"].lower()
