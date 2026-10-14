"""Persistent focus sessions; explicit opt-in for coarse behavior statistics."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_or_create_user, get_session
from .models import BehaviorConsent, BehaviorEvent, FocusSession, Preference, Task, User

router = APIRouter(prefix="/api/v2/focus", tags=["v2-focus"])


class StartFocus(BaseModel):
    task_id: str | None = None
    planned_minutes: int = Field(default=25, ge=1, le=240)


class FinishFocus(BaseModel):
    outcome: str = Field(pattern="^(completed|abandoned)$")


class ConsentInput(BaseModel):
    enabled: bool


def owner_lock(db: Session, uid: str) -> None:
    get_or_create_user(db, uid)
    db.scalar(select(User).where(User.uid == uid).with_for_update())


def session_for_user(db: Session, uid: str, session_id: str, lock: bool = False) -> FocusSession:
    query = select(FocusSession).where(
        FocusSession.id == session_id, FocusSession.owner_uid == uid
    )
    if lock:
        query = query.with_for_update()
    result = db.scalar(query)
    if result is None:
        raise HTTPException(404, "Focus session not found")
    return result


def render(row: FocusSession) -> dict:
    return {
        "id": row.id, "task_id": row.task_id, "status": row.status,
        "planned_seconds": row.planned_seconds, "actual_seconds": row.actual_seconds,
        "started_at": row.started_at, "ended_at": row.ended_at,
    }


def aware(value: datetime) -> datetime:
    return value if value.tzinfo and value.utcoffset() is not None else value.replace(tzinfo=timezone.utc)


@router.post("/sessions", status_code=201)
def start_focus(
    body: StartFocus,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    owner_lock(db, uid)
    if body.task_id:
        task = db.scalar(select(Task.id).where(Task.id == body.task_id, Task.owner_uid == uid))
        if task is None:
            raise HTTPException(404, "Task not found")
    active = db.scalar(select(FocusSession.id).where(
        FocusSession.owner_uid == uid, FocusSession.status == "active"
    ).limit(1))
    if active:
        raise HTTPException(409, "Finish your active focus session before starting another")
    row = FocusSession(
        owner_uid=uid, task_id=body.task_id, planned_seconds=body.planned_minutes * 60,
        status="active", actual_seconds=0, started_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return render(row)


@router.post("/sessions/{session_id}/finish")
def finish_focus(
    session_id: str, body: FinishFocus,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    owner_lock(db, uid)
    row = session_for_user(db, uid, session_id, lock=True)
    if row.status != "active":
        raise HTTPException(409, "This focus session is already closed")
    now = datetime.now(timezone.utc)
    # Elapsed time comes only from the server clock, never from an untrusted
    # browser-reported duration. Cap entries to exclude abandoned overnight tabs.
    elapsed = max(0, int((now - aware(row.started_at)).total_seconds()))
    row.actual_seconds = min(elapsed, row.planned_seconds)
    row.ended_at = now
    row.status = body.outcome

    consent = db.get(BehaviorConsent, uid)
    if consent and consent.enabled and body.outcome == "completed":
        pref = db.get(Preference, uid)
        zone = ZoneInfo(pref.timezone if pref else "Asia/Kolkata")
        db.add(BehaviorEvent(
            owner_uid=uid, kind="focus_completed",
            hour_of_day=aware(row.started_at).astimezone(zone).hour,
            duration_seconds=row.actual_seconds,
            happened_at=now,
        ))
    db.commit()
    db.refresh(row)
    return render(row)


@router.get("/sessions")
def list_focus(
    limit: int = Query(30, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    rows = db.scalars(select(FocusSession).where(
        FocusSession.owner_uid == user["uid"]
    ).order_by(FocusSession.started_at.desc()).limit(limit)).all()
    return [render(row) for row in rows]


@router.get("/consent")
def get_consent(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    consent = db.get(BehaviorConsent, user["uid"])
    return {"enabled": bool(consent and consent.enabled)}


@router.put("/consent")
def set_consent(
    body: ConsentInput,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    owner_lock(db, uid)
    consent = db.get(BehaviorConsent, uid)
    if consent is None:
        consent = BehaviorConsent(owner_uid=uid, enabled=body.enabled)
        db.add(consent)
    else:
        consent.enabled = body.enabled
    consent.updated_at = datetime.now(timezone.utc)
    if not body.enabled:
        # Turning personalization off also clears its derived historical signals.
        db.execute(delete(BehaviorEvent).where(BehaviorEvent.owner_uid == uid))
    db.commit()
    return {"enabled": body.enabled, "past_behavior_removed": not body.enabled}


@router.get("/insights")
def focus_insights(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    sessions = db.scalars(select(FocusSession).where(
        FocusSession.owner_uid == uid,
        FocusSession.status == "completed",
    )).all()
    seconds = sum(session.actual_seconds for session in sessions)
    consent = db.get(BehaviorConsent, uid)
    if not consent or not consent.enabled:
        return {
            "completed_sessions": len(sessions), "completed_minutes": seconds // 60,
            "personalization_enabled": False, "preferred_hour": None,
            "sample_size": 0, "reason": "Behavioral personalization is off",
        }
    rows = db.scalars(select(BehaviorEvent).where(
        BehaviorEvent.owner_uid == uid, BehaviorEvent.kind == "focus_completed"
    )).all()
    counts: dict[int, int] = {}
    for event in rows:
        counts[event.hour_of_day] = counts.get(event.hour_of_day, 0) + event.duration_seconds
    # At least five completed samples are needed before recommending a work hour.
    preferred = max(counts, key=lambda hour: (counts[hour], -hour)) if len(rows) >= 5 and counts else None
    return {
        "completed_sessions": len(sessions), "completed_minutes": seconds // 60,
        "personalization_enabled": True, "preferred_hour": preferred,
        "sample_size": len(rows),
        "reason": "Estimated from completed focus sessions" if preferred is not None else "More sessions needed before estimating preferences",
    }
