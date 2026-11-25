"""Stage 5 tests: cross-feature event-move replanning, atomic multi-record commit, conflict rollback, and guarded undo."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.assistant import router as assistant_router
from v2.db import get_session
from v2.models import Base, FixedEvent, Preference, ScheduleBlock, Task, User
from v2.planning_api import router as planning_router
from v2.proposals_api import router as proposals_router


def _setup_db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


def _client(db: Session, uid: str = "alice"):
    app = FastAPI()
    app.include_router(assistant_router)
    app.include_router(planning_router)
    app.include_router(proposals_router)
    app.dependency_overrides[get_current_user] = lambda: {"uid": uid}
    app.dependency_overrides[get_session] = lambda: db
    return TestClient(app)


def _next_weekday(now_local: datetime, target_weekday: int) -> datetime:
    delta = (target_weekday - now_local.weekday()) % 7
    if delta == 0:
        delta = 7
    return (now_local + timedelta(days=delta)).replace(hour=10, minute=0, second=0, microsecond=0)


def test_moved_exam_replan_atomic_commit_and_guarded_undo():
    engine = _setup_db()
    tz = ZoneInfo("Asia/Kolkata")
    now_local = datetime.now(tz)
    friday_10 = _next_weekday(now_local, 4)  # Friday 10:00 IST
    wednesday_10 = (friday_10 - timedelta(days=2))
    thursday_14 = (friday_10 - timedelta(days=1)).replace(hour=14)

    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(Preference(owner_uid="alice", timezone="Asia/Kolkata", work_start=time(8), work_end=time(22)))
        db.flush()

        exam = FixedEvent(
            owner_uid="alice",
            title="Control Systems exam",
            starts_at=wednesday_10.astimezone(timezone.utc),
            ends_at=(wednesday_10 + timedelta(hours=2)).astimezone(timezone.utc),
        )
        protected = FixedEvent(
            owner_uid="alice",
            title="Protected Lab",
            starts_at=thursday_14.astimezone(timezone.utc),
            ends_at=(thursday_14 + timedelta(hours=1)).astimezone(timezone.utc),
        )
        project_task = Task(owner_uid="alice", title="Project milestone", duration_minutes=60, importance="important")
        study_task = Task(owner_uid="alice", title="Control Systems revision", duration_minutes=30, importance="important")
        db.add_all([exam, protected, project_task, study_task])
        db.flush()

        # Existing project block on Friday 10:00-11:00 (conflicts with moved exam!)
        project_block = ScheduleBlock(
            owner_uid="alice",
            task_id=project_task.id,
            starts_at=friday_10.astimezone(timezone.utc),
            ends_at=(friday_10 + timedelta(hours=1)).astimezone(timezone.utc),
        )
        db.add(project_block)
        db.commit()

        with _client(db, "alice") as client:
            # 1. Missing time asks targeted question
            ask = client.post(
                "/api/v2/assistant/chat",
                json={"message": "My Control Systems exam moved to Friday; reorganize my week"},
            )
            assert ask.status_code == 200
            assert ask.json()["decision"]["kind"] == "answer"
            assert "What time" in ask.json()["decision"]["message"]

            # 2. With time specified, simulates all 3 operations without mutating DB
            sim_resp = client.post(
                "/api/v2/assistant/chat",
                json={"message": f"My Control Systems exam moved to {friday_10.date().isoformat()} at 10:00; reorganize my week"},
            )
            assert sim_resp.status_code == 200
            decision = sim_resp.json()["decision"]
            assert decision["kind"] == "draft_schedule_proposal"
            draft = decision["draft_schedule_proposal"]
            op_types = [op["op_type"] for op in draft["operations"]]
            assert "move_fixed_event" in op_types
            assert "move_schedule_block" in op_types
            assert "add_schedule_block" in op_types

            # Before approval, exam is still on Wednesday
            db.refresh(exam)
            assert exam.starts_at.replace(tzinfo=timezone.utc) == wednesday_10.astimezone(timezone.utc)

            # 3. Approve atomically -> all 3 effects verified, protected event untouched
            app_resp = client.post(
                f"/api/v2/plans/{draft['proposal_id']}/approve",
                json={"expected_revision": draft["revision"], "proposal_digest": draft["proposal_digest"]},
            )
            assert app_resp.status_code == 200, app_resp.text
            assert app_resp.json()["verification_status"] == "verified"

            db.expire_all()
            ev_after = db.get(FixedEvent, exam.id)
            blk_after = db.get(ScheduleBlock, project_block.id)
            prot_after = db.get(FixedEvent, protected.id)
            study_blocks = db.scalars(select(ScheduleBlock).where(ScheduleBlock.task_id == study_task.id)).all()
            assert ev_after.starts_at.replace(tzinfo=timezone.utc) == friday_10.astimezone(timezone.utc)
            assert blk_after.starts_at.replace(tzinfo=timezone.utc) != friday_10.astimezone(timezone.utc)
            assert len(study_blocks) == 1
            assert prot_after.starts_at.replace(tzinfo=timezone.utc) == thursday_14.astimezone(timezone.utc)

            # 4. Guarded undo restores original positions and removes added study block
            undo_resp = client.post(f"/api/v2/plans/{draft['proposal_id']}/undo")
            assert undo_resp.status_code == 200, undo_resp.text
            assert undo_resp.json()["status"] == "undone"
            db.expire_all()
            assert db.get(FixedEvent, exam.id).starts_at.replace(tzinfo=timezone.utc) == wednesday_10.astimezone(timezone.utc)
            assert db.get(ScheduleBlock, project_block.id).starts_at.replace(tzinfo=timezone.utc) == friday_10.astimezone(timezone.utc)
            assert db.scalars(select(ScheduleBlock).where(ScheduleBlock.task_id == study_task.id)).all() == []


def test_stale_or_conflicting_operation_rolls_back_all_three():
    engine = _setup_db()
    tz = ZoneInfo("Asia/Kolkata")
    friday_10 = _next_weekday(datetime.now(tz), 4)
    wednesday_10 = friday_10 - timedelta(days=2)

    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.add(Preference(owner_uid="alice", timezone="Asia/Kolkata", work_start=time(8), work_end=time(22)))
        db.flush()
        exam = FixedEvent(
            owner_uid="alice", title="Control Systems exam",
            starts_at=wednesday_10.astimezone(timezone.utc),
            ends_at=(wednesday_10 + timedelta(hours=2)).astimezone(timezone.utc),
        )
        t1 = Task(owner_uid="alice", title="Project", duration_minutes=60)
        t2 = Task(owner_uid="alice", title="Study", duration_minutes=30)
        db.add_all([exam, t1, t2])
        db.flush()
        blk = ScheduleBlock(
            owner_uid="alice", task_id=t1.id,
            starts_at=friday_10.astimezone(timezone.utc),
            ends_at=(friday_10 + timedelta(hours=1)).astimezone(timezone.utc),
        )
        db.add(blk)
        db.commit()

        with _client(db, "alice") as client:
            sim_resp = client.post(
                "/api/v2/assistant/chat",
                json={"message": f"My Control Systems exam moved to {friday_10.date().isoformat()} at 10:00; reorganize my week"},
            )
            draft = sim_resp.json()["decision"]["draft_schedule_proposal"]

            # Inject a stale version on the project block before approval
            blk.version += 1
            db.commit()

            fail_resp = client.post(
                f"/api/v2/plans/{draft['proposal_id']}/approve",
                json={"expected_revision": draft["revision"], "proposal_digest": draft["proposal_digest"]},
            )
            assert fail_resp.status_code == 409
            db.expire_all()
            # All 3 remain unapplied!
            assert db.get(FixedEvent, exam.id).starts_at.replace(tzinfo=timezone.utc) == wednesday_10.astimezone(timezone.utc)
            assert db.get(ScheduleBlock, blk.id).starts_at.replace(tzinfo=timezone.utc) == friday_10.astimezone(timezone.utc)
            assert db.scalars(select(ScheduleBlock).where(ScheduleBlock.task_id == t2.id)).all() == []
