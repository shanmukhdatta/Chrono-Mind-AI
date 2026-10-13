"""Configuration tests require no Firebase, LLM, network or test account."""
import pytest

from core.config import get_cors_origins, parse_cors_origins


def test_local_default_origin(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert get_cors_origins() == ["http://localhost:5173"]


def test_explicit_origin_list_is_trimmed_and_deduplicated(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:5173, https://example.test:443, http://localhost:5173",
    )
    assert get_cors_origins() == [
        "http://localhost:5173",
        "https://example.test:443",
    ]


@pytest.mark.parametrize("value", [
    "", " ", "*", "null", "http://localhost:5173/",
    "https://example.test/admin", "https://example.test?key=secret",
    "https://user:password@example.test", "javascript://example.test",
    "https://example.test:invalid", "http://localhost:5173,",
])
def test_invalid_or_unsafe_origins_are_rejected(value):
    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        parse_cors_origins(value)
