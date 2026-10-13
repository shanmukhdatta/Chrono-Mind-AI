"""Fail-closed admin, token bootstrap and error disclosure checks."""
import asyncio

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from middleware import auth


def invoke(coroutine):
    return asyncio.run(coroutine)


@pytest.mark.parametrize("configured", ["", " ", "your_firebase_uid_here"])
def test_admin_denied_when_not_configured(monkeypatch, configured):
    monkeypatch.setenv("ADMIN_UID", configured)
    with pytest.raises(HTTPException) as exc:
        invoke(auth.get_admin_user({"uid": "ordinary_user"}))
    assert exc.value.status_code == 403


def test_admin_requires_matching_uid(monkeypatch):
    monkeypatch.setenv("ADMIN_UID", "admin123")
    with pytest.raises(HTTPException) as exc:
        invoke(auth.get_admin_user({"uid": "ordinary_user"}))
    assert exc.value.status_code == 403
    assert invoke(auth.get_admin_user({"uid": "admin123"}))["uid"] == "admin123"


def test_missing_token_is_rejected():
    with pytest.raises(HTTPException) as exc:
        invoke(auth.get_current_user(None))
    assert exc.value.status_code == 401


def test_firebase_initializes_before_verifying(monkeypatch):
    calls = []
    monkeypatch.setattr(auth, "ensure_firebase_app", lambda: calls.append("init"))
    def verified(token, check_revoked=False):
        calls.append(("verify", token, check_revoked))
        return {"uid": "u123"}
    monkeypatch.setattr(auth.firebase_auth, "verify_id_token", verified)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    assert invoke(auth.get_current_user(credentials))["uid"] == "u123"
    assert calls == ["init", ("verify", "token", True)]


def test_invalid_token_does_not_leak_verification_details(monkeypatch):
    monkeypatch.setattr(auth, "ensure_firebase_app", lambda: object())
    def rejected(token, check_revoked=False):
        raise RuntimeError("private auth configuration detail")
    monkeypatch.setattr(auth.firebase_auth, "verify_id_token", rejected)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad")
    with pytest.raises(HTTPException) as exc:
        invoke(auth.get_current_user(credentials))
    assert exc.value.status_code == 401
    assert "private" not in exc.value.detail

@pytest.mark.parametrize(
    ("failure_kind", "expected_detail"),
    [
        ("expired", "Token expired. Please sign in again."),
        ("revoked", "Token revoked. Please sign in again."),
    ],
)
def test_expired_and_revoked_tokens_are_rejected_without_leaks(
    monkeypatch, failure_kind, expected_detail
):
    """Exercise fail-closed exception branches; not a live Firebase test."""
    class ExpiredTestToken(Exception):
        pass

    class RevokedTestToken(Exception):
        pass

    monkeypatch.setattr(auth, "ensure_firebase_app", lambda: object())
    monkeypatch.setattr(auth.firebase_auth, "ExpiredIdTokenError", ExpiredTestToken)
    monkeypatch.setattr(auth.firebase_auth, "RevokedIdTokenError", RevokedTestToken)
    failure = ExpiredTestToken if failure_kind == "expired" else RevokedTestToken

    def reject(token, check_revoked=False):
        assert token == "test-token"
        assert check_revoked is True
        raise failure("confidential verifier diagnostics")

    monkeypatch.setattr(auth.firebase_auth, "verify_id_token", reject)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-token")
    with pytest.raises(HTTPException) as exc:
        invoke(auth.get_current_user(credentials))
    assert exc.value.status_code == 401
    assert exc.value.detail == expected_detail
    assert "confidential" not in exc.value.detail
