"""FastAPI lifespan smoke test without any live external integration."""
from fastapi.testclient import TestClient

from main import app


def test_app_lifespan_starts_without_firebase_or_llm_keys(monkeypatch):
    # This proves the web app's HTTP lifespan, not Firebase integration.
    monkeypatch.setenv("CHRONOMIND_DISABLE_LEGACY_SCHEDULER", "1")
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["service"] == "chronomind-ai"
        # Auth remains fail-closed without a bearer token.
        assert client.get("/api/tasks").status_code == 401
