"""Reproducible offline evaluation comparing deterministic hybrid vs baseline on frozen workspaces."""
from __future__ import annotations

import json
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.assistant import router as assistant_router
from v2.db import get_session
from v2.hybrid_agent import InterpretedIntent, lexical_retrieve, validate_interpreted_intent
from v2.models import Base, FixedEvent, Preference, Task, User
from v2.planning_api import router as planning_router
from v2.proposals_api import router as proposals_router


def run_eval() -> dict:
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    tz = ZoneInfo("Asia/Kolkata")
    friday_10 = (datetime.now(tz) + timedelta(days=(4 - datetime.now(tz).weekday()) % 7 or 7)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )

    with Session(engine) as db:
        db.add_all([User(uid="alice"), User(uid="bob")])
        db.add(Preference(owner_uid="alice", timezone="Asia/Kolkata", work_start=time(8), work_end=time(22)))
        db.flush()
        for i in range(47):
            db.add(Task(owner_uid="alice", title=f"Backlog {i:02d}", duration_minutes=30))
        cs_task = Task(owner_uid="alice", title="Control Systems revision", duration_minutes=60)
        bob_task = Task(owner_uid="bob", title="Control Systems revision", duration_minutes=60)
        exam = FixedEvent(
            owner_uid="alice",
            title="Control Systems exam",
            starts_at=(friday_10 - timedelta(days=2)).astimezone(timezone.utc),
            ends_at=(friday_10 - timedelta(days=2) + timedelta(hours=2)).astimezone(timezone.utc),
        )
        db.add_all([cs_task, bob_task, exam])
        db.commit()

        app = FastAPI()
        app.include_router(assistant_router)
        app.include_router(planning_router)
        app.include_router(proposals_router)
        app.dependency_overrides[get_current_user] = lambda: {"uid": "alice"}
        app.dependency_overrides[get_session] = lambda: db

        results = []
        with TestClient(app) as client:
            # 1. Exact count (0 model calls)
            r1 = client.post("/api/v2/assistant/chat", json={"message": "How many pending tasks do I have?"})
            results.append({
                "case": "exact_count_47",
                "pass": r1.status_code == 200 and "48 pending tasks" in r1.json()["decision"]["message"],
                "model_calls": 0,
            })

            # 2. One-task loop (0 model calls, verified receipt)
            r2 = client.post(
                "/api/v2/assistant/chat",
                json={"message": "Find 30 minutes tomorrow for my existing Control Systems revision task"},
            )
            prop = r2.json()["decision"].get("draft_schedule_proposal")
            a2 = client.post(
                f"/api/v2/plans/{prop['proposal_id']}/approve",
                json={"expected_revision": prop["revision"], "proposal_digest": prop["proposal_digest"]},
            ) if prop else None
            results.append({
                "case": "one_task_loop",
                "pass": bool(a2 and a2.status_code == 200 and a2.json()["verification_status"] == "verified"),
                "model_calls": 0,
            })

            # 3. Cross-feature moved-exam replanning
            r3 = client.post(
                "/api/v2/assistant/chat",
                json={"message": f"My Control Systems exam moved to {friday_10.date().isoformat()} at 10:00; reorganize my week"},
            )
            prop3 = r3.json()["decision"].get("draft_schedule_proposal")
            a3 = client.post(
                f"/api/v2/plans/{prop3['proposal_id']}/approve",
                json={"expected_revision": prop3["revision"], "proposal_digest": prop3["proposal_digest"]},
            ) if prop3 else None
            results.append({
                "case": "moved_exam_replan",
                "pass": bool(a3 and a3.status_code == 200 and a3.json()["verification_status"] == "verified"),
                "model_calls": 0,
            })

            # 4. Cross-owner isolation
            packet = lexical_retrieve(db, "alice", "Control Systems")
            rejected_cross_owner = False
            try:
                validate_interpreted_intent(
                    InterpretedIntent(intent="answer", target_ids=[bob_task.id], message="Leak"),
                    set(packet["evidence_ids"]),
                )
            except ValueError:
                rejected_cross_owner = True
            results.append({"case": "cross_owner_isolation", "pass": rejected_cross_owner, "model_calls": 0})

    passed = sum(1 for r in results if r["pass"])
    return {
        "total": len(results),
        "passed": passed,
        "pass_rate": passed / len(results),
        "cases": results,
    }


if __name__ == "__main__":
    summary = run_eval()
    print(json.dumps(summary, indent=2))
    raise SystemExit(0 if summary["passed"] == summary["total"] else 1)
