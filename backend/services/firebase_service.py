"""Lazy, single-process Firebase Admin initialization.

Server credentials are loaded only on trusted backend processes, never sent to
the frontend. Firebase token verification is explicitly initialized before use.
"""
import json
import os

import firebase_admin
from firebase_admin import credentials, firestore

_db = None


def ensure_firebase_app():
    """Return the initialized default Firebase app or fail clearly."""
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    cred_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "").strip()
    if cred_json:
        cred_dict = json.loads(cred_json)
        if not isinstance(cred_dict, dict):
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON must be a JSON object")
        credential = credentials.Certificate(cred_dict)
    elif cred_path:
        credential = credentials.Certificate(cred_path)
    else:
        raise ValueError("Firebase service account credentials are not configured")

    # Firebase Admin protects default-app initialization against competing callers.
    try:
        return firebase_admin.initialize_app(credential)
    except ValueError:
        # Another caller may have finished initialization while we were loading.
        return firebase_admin.get_app()


def init_firebase():
    ensure_firebase_app()
    return firestore.client()


def get_db():
    global _db
    if _db is None:
        _db = init_firebase()
    return _db
