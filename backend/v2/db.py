"""Lazy database wiring. Importing the legacy app never connects to Postgres."""
import os

from dotenv import load_dotenv
load_dotenv(override=False)
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@lru_cache(maxsize=1)
def engine():
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)


def get_session():
    try:
        factory = sessionmaker(bind=engine(), expire_on_commit=False)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(503, "V2 database is not configured") from exc
    with factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def get_or_create_user(session: Session, uid: str):
    from .models import User
    user = session.get(User, uid)
    if user is None:
        user = User(uid=uid)
        session.add(user)
        session.flush()
    return user
