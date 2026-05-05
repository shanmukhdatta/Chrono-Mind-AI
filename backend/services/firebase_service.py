import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

_db = None

def init_firebase():
    if not firebase_admin._apps:
        # Support both file path and JSON string env var (for deployment)
        cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
        cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")

        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
        elif cred_path:
            cred = credentials.Certificate(cred_path)
        else:
            raise ValueError(
                "Set FIREBASE_SERVICE_ACCOUNT_PATH or FIREBASE_SERVICE_ACCOUNT_JSON env var"
            )

        firebase_admin.initialize_app(cred)
    return firestore.client()

def get_db():
    global _db
    if _db is None:
        _db = init_firebase()
    return _db
