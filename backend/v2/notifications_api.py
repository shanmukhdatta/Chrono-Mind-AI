"""Idempotent in-app deadline notifications and strictly user-owned read APIs."""
from datetime import datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_session
from .models import InAppNotification, Preference, Task, User

router = APIRouter(prefix="/api/v2/notifications", tags=["v2-notifications"])


def as_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None and value.utcoffset() is not None else value.replace(tzinfo=timezone.utc)


def create_daily_notifications(db: Session, uid: str, now: datetime | None = None) -> int:
    """Create task notifications once per user/local-day. Caller owns transaction."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must contain a timezone")
    # The owner row lock serializes writers and prevents duplicate creation.
    owner = db.scalar(select(User).where(User.uid == uid).with_for_update())
    if owner is None:
        raise ValueError("User must exist before notification generation")
    pref = db.get(Preference, uid)
    zone = ZoneInfo(pref.timezone if pref else owner.timezone)
    local_today = now.astimezone(zone).date()
    tomorrow = datetime.combine(local_today + timedelta(days=1), time.min, zone).astimezone(timezone.utc)
    rows = db.scalars(select(Task).where(
        Task.owner_uid == uid, Task.status == "pending", Task.deadline_at.is_not(None)
    ).order_by(Task.deadline_at).limit(100)).all()
    existing_keys = set(db.scalars(select(InAppNotification.dedupe_key).where(
        InAppNotification.owner_uid == uid,
        InAppNotification.created_at >= now - timedelta(days=30),
    )).all())
    made = 0
    for task in rows:
        due = as_aware(task.deadline_at)
        if due >= tomorrow:
            continue
        category = "overdue" if due < now else "due_today"
        key = f"{local_today.isoformat()}:{category}:{task.id}"
        if key in existing_keys:
            continue
        text = ("Overdue task: " if category == "overdue" else "Due soon: ") + task.title
        db.add(InAppNotification(
            owner_uid=uid, kind=category, dedupe_key=key,
            source_task_id=task.id, message=text[:300],
            created_at=now,
        ))
        made += 1
        existing_keys.add(key)
    db.flush()
    return made


def present(row: InAppNotification):
    return {
        "id": row.id, "kind": row.kind, "message": row.message,
        "source_task_id": row.source_task_id, "created_at": row.created_at,
        "read_at": row.read_at,
    }


@router.get("")
def list_notifications(
    unread_only: bool = False,
    limit: int = Query(40, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    query = select(InAppNotification).where(InAppNotification.owner_uid == uid)
    if unread_only:
        query = query.where(InAppNotification.read_at.is_(None))
    rows = db.scalars(query.order_by(InAppNotification.created_at.desc()).limit(limit)).all()
    return [present(row) for row in rows]


@router.get("/unread-count")
def unread_count(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    number = db.scalar(select(func.count()).select_from(InAppNotification).where(
        InAppNotification.owner_uid == user["uid"],
        InAppNotification.read_at.is_(None)
    ))
    return {"unread_count": number or 0}


@router.post("/{notification_id}/read")
def mark_read(notification_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    row = db.scalar(select(InAppNotification).where(
        InAppNotification.id == notification_id,
        InAppNotification.owner_uid == user["uid"]
    ))
    if row is None:
        raise HTTPException(404, "Notification not found")
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
    return present(row)


@router.post("/mark-all-read")
def read_all(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    result = db.execute(update(InAppNotification).where(
        InAppNotification.owner_uid == user["uid"],
        InAppNotification.read_at.is_(None)
    ).values(read_at=datetime.now(timezone.utc)))
    db.commit()
    return {"marked_read": result.rowcount}
