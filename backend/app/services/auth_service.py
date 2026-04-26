"""
ChronoMind AI — Authentication Service (JWT + Google OAuth)
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.config import settings
from app.models.models import User
from app.models.schemas import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Password ─────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── JWT ──────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


# ─── User lookup ──────────────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


# ─── Google OAuth ─────────────────────────────────────────────────

async def exchange_google_code(code: str, redirect_uri: str) -> dict:
    """Exchange auth code for Google tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_google_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_or_create_google_user(db: AsyncSession, google_info: dict) -> User:
    """Find existing user or create from Google profile."""
    # Try by google_id first
    result = await db.execute(
        select(User).where(User.google_id == google_info["id"])
    )
    user = result.scalar_one_or_none()

    if user:
        # Update avatar if changed
        user.avatar_url = google_info.get("picture")
        return user

    # Try by email
    result = await db.execute(
        select(User).where(User.email == google_info["email"])
    )
    user = result.scalar_one_or_none()

    if user:
        user.google_id = google_info["id"]
        user.avatar_url = google_info.get("picture")
        return user

    # Create new
    user = User(
        email=google_info["email"],
        name=google_info.get("name", "Student"),
        google_id=google_info["id"],
        avatar_url=google_info.get("picture"),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
