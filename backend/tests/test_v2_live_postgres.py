"""Real PostgreSQL acceptance: migrations, approval transactions and graph recovery.

Runs only in disposable PostgreSQL CI; never against user or production data.
"""
import os
from datetime import datetime, time, timedelta, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import Command
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from v2.agent_graph import build_planner_graph
from v2.agent_api import checkpoint_uri
from v2.db import engine, get_session
from v2.models import PlanProposal, ScheduleBlock, Task, User
from v2.proposals_api import router as proposals_router

pytestmark = pytest.mark.skipif(
    os.getenv("CHRONOMIND_LIVE_PG_TEST") != "1",
    reason="Only run in explicitly enabled, disposable PostgreSQL CI",
)


def test_alembic_schema_and_approval_undo_persist_full_plan_source():
    dbengine = engine()
    with dbengine.connect() as connection:
        head = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert head == "0013_focus_context"
    columns = inspect(dbengine).get_columns("v2_schedule_blocks")
    source = next(column for column in columns if column["name"] == "source")
    assert source["type"].length >= 41, "plan UUID source must fit Postgres VARCHAR"

    uid = "ci-alice-" + str(uuid4())
    other = "ci-bob-" + str(uuid4())
    local = datetime.now(ZoneInfo("Asia/Kolkata"))
    future = datetime.combine(local.date() + timedelta(days=1), time(10), ZoneInfo("Asia/Kolkata"))
    begins = future.astimezone(timezone.utc)
    ends = begins + timedelta(minutes=30)
    with Session(dbengine) as db:
        db.add_all([User(uid=uid), User(uid=other)])
        db.flush()
        task = Task(owner_uid=uid, title="Postgres approval check", duration_minutes=30)
        db.add(task)
        db.flush()
        proposal = PlanProposal(
            owner_uid=uid,
            proposed_blocks=[{
                "task_id": task.id, "title": task.title,
                "starts_at": begins.isoformat(), "ends_at": ends.isoformat(),
                "duration_minutes": 30,
            }],
            unscheduled=[],
            task_versions={task.id: task.version},
            preferences_snapshot={
                "timezone": "Asia/Kolkata", "work_start": "08:00", "work_end": "22:00",
                "max_daily_minutes": 480, "min_break_minutes": 10,
            },
            committed_block_ids=[],
            created_at=datetime.now(timezone.utc),
        )
        db.add(proposal)
        db.commit()
        plan_id = proposal.id

    application = FastAPI()
    application.include_router(proposals_router)
    current = {"uid": other}
    application.dependency_overrides[get_current_user] = lambda: current

    def session_override():
        with Session(dbengine) as db:
            yield db
    application.dependency_overrides[get_session] = session_override
    browser = TestClient(application)
    assert browser.get(f"/api/v2/plans/{plan_id}").status_code == 404

    current["uid"] = uid
    response = browser.post(f"/api/v2/plans/{plan_id}/approve")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "approved"
    with Session(dbengine) as db:
        blocks = db.scalars(select(ScheduleBlock).where(
            ScheduleBlock.owner_uid == uid
        )).all()
        assert len(blocks) == 1
        assert blocks[0].source == "plan:" + plan_id
    assert browser.post(f"/api/v2/plans/{plan_id}/approve").status_code == 409
    undone = browser.post(f"/api/v2/plans/{plan_id}/undo")
    assert undone.status_code == 200, undone.text
    assert undone.json()["status"] == "undone"
    with Session(dbengine) as db:
        assert not db.scalars(select(ScheduleBlock).where(
            ScheduleBlock.owner_uid == uid
        )).all()


def test_checkpoint_survives_closing_and_reopening_postgres_connection():
    run_id = str(uuid4())
    state = {"owner_uid": "ci-" + run_id, "run_id": run_id, "days": 3}
    config = {"configurable": {"thread_id": "ci:" + run_id}}
    calls = []
    preview = {
        "blocks": [{
            "task_id": "task", "title": "Practice", "duration_minutes": 30,
            "starts_at": "2026-12-01T08:00:00+00:00",
            "ends_at": "2026-12-01T08:30:00+00:00",
        }],
        "unscheduled": [],
    }
    def load(uid, days):
        return preview

    def store(uid, identifier, value):
        calls.append(identifier)
        return identifier

    with PostgresSaver.from_conn_string(checkpoint_uri()) as saver:
        graph = build_planner_graph(load, store, saver)
        output = graph.invoke(state, config)
        assert output["status"] == "awaiting_review"
        assert graph.get_state(config).next == ("await_human",)
        assert calls == [run_id]

    # This is a fresh DB connection and a fresh compiled graph (not an in-memory saver).
    with PostgresSaver.from_conn_string(checkpoint_uri()) as saver:
        recovered = build_planner_graph(load, store, saver)
        snapshot = recovered.get_state(config)
        assert snapshot.values["proposal_id"] == run_id
        assert snapshot.next == ("await_human",)
        finished = recovered.invoke(Command(resume="rejected"), config)
        assert finished["status"] == "rejected"
        assert calls == [run_id], "Checkpoint replay must not persist a second proposal"
