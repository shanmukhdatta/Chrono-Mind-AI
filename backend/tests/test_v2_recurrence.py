"""Recurrence generation is bounded, idempotent and avoids destructive skips."""
from datetime import date, time

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from middleware.auth import get_current_user
from v2.db import get_session
from v2.models import Base, RecurrenceOccurrence, RecurrenceSeries, Task
from v2.recurrence import SeriesInput, upcoming_dates, router


def test_weekdays_are_deterministic():
    class Fake:
        start_date = date(2026, 10, 12)
        end_date = date(2026, 10, 19)
        frequency = "weekly"
        weekdays = "0,2"
    assert list(upcoming_dates(Fake(), date(2026, 10, 12), 7)) == [
        date(2026, 10, 12), date(2026, 10, 14)
    ]


def test_schema_rejects_invalid_weekday_and_date():
    import pytest
    with pytest.raises(ValueError):
        SeriesInput(title="Routine", frequency="weekly", weekdays=[8], start_date=date.today(), duration_minutes=45)
    with pytest.raises(ValueError):
        SeriesInput(title="Routine", frequency="daily", start_date=date(2026, 10, 15), end_date=date(2026, 10, 14), duration_minutes=45)


def test_series_materialize_is_idempotent_and_tenant_scoped():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        app = FastAPI()
        app.include_router(router)
        principal = {"uid": "alice"}
        app.dependency_overrides[get_current_user] = lambda: principal
        def get_db():
            with Session(engine) as session:
                yield session
        app.dependency_overrides[get_session] = get_db
        client = TestClient(app)
        from datetime import datetime
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
        body = {
            "title": "Language practice", "duration_minutes": 25,
            "frequency": "daily", "start_date": today.isoformat(),
            "due_time": "19:00:00", "timezone": "Asia/Kolkata"
        }
        created = client.post("/api/v2/recurrence", json=body)
        assert created.status_code == 201, created.text
        key = created.json()["id"]
        principal["uid"] = "bob"
        assert client.post("/api/v2/recurrence/" + key + "/materialize").status_code == 404
        principal["uid"] = "alice"
        assert client.post("/api/v2/recurrence/" + key + "/materialize", params={"days": 3}).json()["created"] == 3
        assert client.post("/api/v2/recurrence/" + key + "/materialize", params={"days": 3}).json()["created"] == 0
        with Session(engine) as db:
            assert db.query(RecurrenceOccurrence).count() == 3
            assert db.query(Task).count() == 3
        assert client.post("/api/v2/recurrence/" + key + "/pause").json()["active"] is False
        assert client.post("/api/v2/recurrence/" + key + "/materialize").status_code == 409
        assert client.post("/api/v2/recurrence/" + key + "/resume").status_code == 200
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
