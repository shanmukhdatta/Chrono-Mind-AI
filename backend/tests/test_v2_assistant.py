"""Assistant never performs write operations, even for malformed LLM output."""
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.db import get_session
from v2.models import Base, Task, User
from v2.assistant import router, AssistantDecision, DraftTask, fallback


def test_decision_requires_draft_payload():
    import pytest
    with pytest.raises(ValueError):
        AssistantDecision(kind="draft_task", message="Add task")
    with pytest.raises(ValueError):
        DraftTask(title=" ", duration_minutes=10)


def test_assistant_chat_draft_is_noncommitting():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            db.add(User(uid="alice"))
            db.add(Task(owner_uid="alice", title="Existing", duration_minutes=30))
            db.commit()
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: {"uid": "alice"}

        def local_session():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_session] = local_session
        browser = TestClient(app)
        expected = AssistantDecision(
            kind="draft_task", message="Here is a draft; confirm to save.",
            draft_task=DraftTask(title="New task", duration_minutes=45),
        )
        with patch("v2.assistant.llm_decision", return_value=expected):
            response = browser.post("/api/v2/assistant/chat", json={"message": "Add a task"})
        assert response.status_code == 200, response.text
        assert response.json()["changes_committed"] is False
        assert response.json()["decision"]["kind"] == "draft_task"
        with Session(engine) as db:
            assert db.query(Task).count() == 1

        with patch("v2.assistant.llm_decision", side_effect=RuntimeError("No API key")):
            result = browser.post("/api/v2/assistant/chat", json={"message": "What should I do?"})
        assert result.json()["mode"] == "fallback"
        assert result.json()["decision"]["kind"] == "answer"
        with patch("v2.assistant.llm_decision", side_effect=AssertionError("no provider call permitted")):
            offline = browser.post("/api/v2/assistant/chat", json={"message": "List my pending tasks"})
        assert offline.status_code == 200
        assert offline.json()["mode"] == "deterministic"
        assert offline.json()["changes_committed"] is False
        assert browser.get("/api/v2/assistant/briefing").json()["pending_count"] == 1
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()



def test_task_change_draft_requires_exact_safe_operation():
    import pytest
    from v2.assistant import DraftTaskChange
    change = DraftTaskChange(task_id="owned-123", version=2, operation="complete")
    assert change.operation == "complete"
    with pytest.raises(ValueError):
        DraftTaskChange(task_id="a", version=1, operation="update")
    with pytest.raises(ValueError):
        DraftTaskChange(task_id="a", version=1, operation="complete", title="Injected edit")
    with pytest.raises(ValueError):
        DraftTaskChange(task_id="a", version=1, operation="send_payment")
    with pytest.raises(ValueError):
        AssistantDecision(kind="draft_task_change", message="Review operation")


def test_task_change_chat_returns_confirmation_draft_without_writing():
    from v2.assistant import DraftTaskChange
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            db.add(User(uid="alice"))
            row = Task(owner_uid="alice", title="Original", duration_minutes=30)
            db.add(row)
            db.commit()
            task_id = row.id
            task_version = row.version
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_current_user] = lambda: {"uid": "alice"}
        def local_session():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[get_session] = local_session
        expected = AssistantDecision(
            kind="draft_task_change", message="Confirm task completion",
            draft_task_change=DraftTaskChange(
                task_id=task_id, version=task_version, operation="complete"
            )
        )
        with patch("v2.assistant.llm_decision", return_value=expected):
            response = TestClient(app).post(
                "/api/v2/assistant/chat", json={"message": "Mark my original task done"}
            )
        assert response.status_code == 200, response.text
        assert response.json()["decision"]["kind"] == "draft_task_change"
        assert response.json()["changes_committed"] is False
        with Session(engine) as db:
            task = db.get(Task, task_id)
            assert task.status == "pending"
            assert task.version == task_version
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
