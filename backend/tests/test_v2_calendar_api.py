from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.calendar_api import router
from v2.db import get_session
from v2.models import Base


def test_fixed_events_conflict_delete_and_tenant_isolation():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        app = FastAPI()
        app.include_router(router)
        identity = {"uid": "alice"}
        app.dependency_overrides[get_current_user] = lambda: identity

        def db_override():
            with Session(engine) as session:
                yield session

        app.dependency_overrides[get_session] = db_override
        client = TestClient(app)
        first = {"title": "Class", "starts_at": "2026-11-01T08:00:00+00:00", "ends_at": "2026-11-01T10:00:00+00:00"}
        response = client.post("/api/v2/fixed-events", json=first)
        assert response.status_code == 201, response.text
        event_id = response.json()["id"]
        overlap = {**first, "title": "Overlap", "starts_at": "2026-11-01T09:00:00+00:00"}
        assert client.post("/api/v2/fixed-events", json=overlap).status_code == 409
        touching = {**first, "title": "After", "starts_at": "2026-11-01T10:00:00+00:00", "ends_at": "2026-11-01T11:00:00+00:00"}
        assert client.post("/api/v2/fixed-events", json=touching).status_code == 201
        params = {"starts_at": "2026-11-01T00:00:00+00:00", "ends_at": "2026-11-02T00:00:00+00:00"}
        assert len(client.get("/api/v2/calendar", params=params).json()["fixed_events"]) == 2
        assert client.get("/api/v2/calendar", params={**params, "ends_at": "2027-01-01T00:00:00+00:00"}).status_code == 422
        assert client.post("/api/v2/fixed-events", json={**first, "starts_at": "2026-11-01T08:00:00"}).status_code == 422
        identity["uid"] = "bob"
        assert client.get("/api/v2/calendar", params=params).json()["fixed_events"] == []
        assert client.delete("/api/v2/fixed-events/" + event_id).status_code == 404
        identity["uid"] = "alice"
        assert client.delete("/api/v2/fixed-events/" + event_id).status_code == 204
        assert len(client.get("/api/v2/calendar", params=params).json()["fixed_events"]) == 1
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
