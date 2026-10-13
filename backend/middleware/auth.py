"""Firebase authentication and fail-closed administrator authorization."""
import logging
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from services.firebase_service import ensure_firebase_app

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required",
        )

    try:
        # Authentication must work before any Firestore route has initialized Firebase.
        ensure_firebase_app()
    except (ValueError, OSError) as exc:
        logger.error("Firebase configuration failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from exc

    try:
        # Firebase Admin verifies signature, issuer, audience, expiration and revocation.
        decoded = firebase_auth.verify_id_token(
            credentials.credentials, check_revoked=True
        )
    except firebase_auth.ExpiredIdTokenError as exc:
        raise HTTPException(status_code=401, detail="Token expired. Please sign in again.") from exc
    except firebase_auth.RevokedIdTokenError as exc:
        raise HTTPException(status_code=401, detail="Token revoked. Please sign in again.") from exc
    except Exception as exc:
        logger.warning("Firebase ID token verification failed: %s", type(exc).__name__)
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

    uid = decoded.get("uid")
    if not isinstance(uid, str) or not uid:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return decoded


async def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    # An unset/placeholder ADMIN_UID must NEVER grant administrator access.
    admin_uid = os.getenv("ADMIN_UID", "").strip()
    if not admin_uid or admin_uid == "your_firebase_uid_here":
        raise HTTPException(status_code=403, detail="Admin access not configured")
    if current_user.get("uid") != admin_uid:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
