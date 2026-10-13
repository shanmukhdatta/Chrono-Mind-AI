"""Process configuration shared by HTTP entrypoints.

Environment variables always take precedence over backend/.env. No credentials
are loaded into the frontend or printed to logs.
"""
import os
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv(override=False)

DEFAULT_CORS_ORIGIN = "http://localhost:5173"


def parse_cors_origins(raw: str) -> list[str]:
    """Return explicit browser origins; wildcard is unsafe with credentials."""
    parts = [entry.strip() for entry in raw.split(",")]
    if not parts or any(not part for part in parts):
        raise ValueError("CORS_ORIGINS must contain non-empty origins")

    unique: list[str] = []
    for origin in parts:
        parsed = urlsplit(origin)
        try:
            valid_port = parsed.port is None or 0 < parsed.port < 65536
        except ValueError:
            valid_port = False
        if (
            origin in ("*", "null")
            or parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or not valid_port
        ):
            raise ValueError("CORS_ORIGINS must contain HTTP(S) origins without paths or credentials")
        if origin not in unique:
            unique.append(origin)
    return unique


def get_cors_origins() -> list[str]:
    """Read once when the application is constructed."""
    return parse_cors_origins(os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGIN))
