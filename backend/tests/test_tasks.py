import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

# Mock Firebase auth
def mock_get_current_user():
    return {"uid": "test_user_123", "email": "test@example.com"}

@pytest.fixture
def mock_user():
    return {"uid": "test_user_123", "email": "test@example.com"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_task_validation():
    with patch('middleware.auth.get_current_user', return_value=mock_get_current_user()):
        # Missing title
        response = client.post("/api/tasks", json={
            "date": "2026-05-05",
            "start_time": "10:00",
            "end_time": "11:00",
            "importance": "important"
        }, headers={"Authorization": "Bearer test_token"})
        assert response.status_code == 422

def test_create_task_end_before_start():
    with patch('middleware.auth.get_current_user', return_value=mock_get_current_user()):
        response = client.post("/api/tasks", json={
            "title": "Test Task",
            "date": "2026-05-05",
            "start_time": "11:00",
            "end_time": "10:00",
            "importance": "important"
        }, headers={"Authorization": "Bearer test_token"})
        assert response.status_code == 400

# Add more tests as needed
