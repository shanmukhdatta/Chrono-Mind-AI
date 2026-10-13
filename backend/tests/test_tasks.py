"""HTTP smoke tests without Firebase credentials or network calls."""
import pytest
from fastapi.testclient import TestClient
from main import app
from middleware.auth import get_current_user


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: {
        "uid": "test_user_123", "email": "test@example.com"
    }
    try:
        # Do not enter TestClient lifespan; these tests must not start nightly jobs.
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_missing_title_is_422(client):
    response = client.post("/api/tasks", json={
        "date": "2026-05-05", "start_time": "10:00", "end_time": "11:00"
    })
    assert response.status_code == 422


def test_end_before_start_is_422(client):
    response = client.post("/api/tasks", json={
        "title": "Test Task", "date": "2026-05-05",
        "start_time": "11:00", "end_time": "10:00"
    })
    assert response.status_code == 422


def test_date_range_requires_both_bounds(client):
    response = client.get("/api/tasks?date_from=2026-10-01")
    assert response.status_code == 422


def test_status_query_is_not_arbitrary(client):
    response = client.get("/api/tasks?status=other")
    assert response.status_code == 422
