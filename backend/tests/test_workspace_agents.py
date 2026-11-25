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
