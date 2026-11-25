import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from v2.models import Base, User, Task
from v2.workspace_agents import Dispatch, Finding, investigate, retrieve


def test_scoped_search_and_cited_handoff():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([User(uid="a"), User(uid="b")])
        db.flush()
        db.add_all([Task(owner_uid="a", title="Math"), Task(owner_uid="b", title="Private math")])
        db.commit()
        def call(role, data, schema):
            if schema is Dispatch:
                return Dispatch(domains=["work","focus"])
            assert "Private math" not in str(data)
            key = next(iter(data["evidence"]))
            return Finding(answer="Retrieved evidence.", sources=[key])
        result = investigate("math", lambda d: retrieve(db, "a", d, "math"), call)
        assert result["specialists"] == ["work","focus"]
        assert result["sources"]["focus/consent"] == {"enabled":False}
        assert not result["changes_committed"]


def test_fabricated_citation_rejected():
    def call(role, data, schema):
        return Dispatch(domains=["work"]) if schema is Dispatch else Finding(answer="Math",sources=["fake"])
    with pytest.raises(ValueError, match="evidence reference"):
        investigate("Math", lambda _: {"task/1":{"title":"Math"}}, call)



def test_authenticated_http_entrypoint_and_all_read_tools(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy.pool import StaticPool
    from middleware.auth import get_current_user
    from v2.assistant import router
    from v2.db import get_session
    from v2 import workspace_agents as agents

    engine = create_engine("sqlite://", poolclass=StaticPool,
                           connect_args={"check_same_thread":False})
    Base.metadata.create_all(engine)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: {"uid":"alice"}
    with Session(engine) as db:
        db.add(User(uid="alice"))
        db.flush()
        db.add(Task(owner_uid="alice", title="Review optics", duration_minutes=30))
        db.commit()
        app.dependency_overrides[get_session] = lambda: db
        calls = []
        def invoke(role, payload, schema):
            calls.append(schema)
            if schema is Dispatch:
                return Dispatch(domains=["planning","progress"])
            return Finding(answer="Evidence retrieved.", sources=[next(iter(payload["evidence"]))])
        monkeypatch.setattr(agents, "provider", lambda: invoke)
        with TestClient(app) as client:
            response = client.post("/api/v2/assistant/investigate", json={"message":"Explain my week"})
        assert response.status_code == 200, response.text
        assert response.json()["changes_committed"] is False
        assert calls == [Dispatch, Finding, Finding]
        for domain in agents.ROLES:
            assert isinstance(retrieve(db, "alice", domain, "optics"), dict)
