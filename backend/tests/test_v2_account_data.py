"""Export includes only the verified user's PostgreSQL-owned records."""
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.account_data import router
from v2.db import get_session
from v2.models import Base, Goal, Task, User


def test_export_scopes_all_tables_to_verified_user():
    engine = create_engine(
        "sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            db.add_all([User(uid="alice"), User(uid="bob")])
            db.add(Goal(owner_uid="bob", title="Secret"))
            db.add(Task(owner_uid="alice", title="Python", duration_minutes=45))
            db.add(Task(owner_uid="bob", title="Private task", duration_minutes=30))
            db.commit()
        app = FastAPI()
        app.include_router(router)
        principal = {"uid": "alice"}
        app.dependency_overrides[get_current_user] = lambda: principal

        def testing_session():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_session] = testing_session
        client = TestClient(app)
        result = client.get("/api/v2/account/export")
        assert result.status_code == 200, result.text
        assert result.headers["cache-control"].startswith("private, no-store")
        body = result.json()
        assert body["owner_uid"] == "alice"
        assert len(body["data"]["tasks"]) == 1
        assert body["data"]["tasks"][0]["title"] == "Python"
        assert body["data"]["goals"] == []
        assert "Secret" not in result.text
        assert "Private task" not in result.text
        assert any("Firestore" in warning for warning in body["limitations"])
        principal["uid"] = "bob"
        result = client.get("/api/v2/account/export").json()
        assert len(result["data"]["tasks"]) == 1
        assert result["data"]["goals"][0]["title"] == "Secret"
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
