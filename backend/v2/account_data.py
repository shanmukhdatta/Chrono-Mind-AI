"""Authenticated read-only, bounded export of ChronoMind V2 PostgreSQL records.

The legacy Firestore dataset and the LangGraph checkpoint tables are separate
data stores. This export deliberately does not pretend to cover them.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_session
from .models import (
    BehaviorConsent, BehaviorEvent, FixedEvent, FocusSession,
    Goal, InAppNotification, LegacyTaskArchive, PlanProposal, Preference,
    RecurrenceOccurrence, RecurrenceSeries, RecurrenceSkip, ScheduleBlock, Task, User,
)

router = APIRouter(prefix="/api/v2/account", tags=["v2-account"])

_EXPORT_TABLES = (
    ("users", User), ("goals", Goal), ("tasks", Task),
    ("schedule_blocks", ScheduleBlock), ("fixed_events", FixedEvent),
    ("preferences", Preference), ("planning_proposals", PlanProposal),
    ("recurrence_series", RecurrenceSeries),
    ("recurrence_occurrences", RecurrenceOccurrence), ("recurrence_skips", RecurrenceSkip),
    ("focus_sessions", FocusSession), ("behavior_consent", BehaviorConsent),
    ("behavior_events", BehaviorEvent), ("in_app_notifications", InAppNotification),
    ("legacy_task_archive", LegacyTaskArchive),
)
_MAX_PER_TABLE = 5000


@router.get("/export")
def export_postgres_data(
    response: Response,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    export: dict[str, list[dict]] = {}
    for name, model in _EXPORT_TABLES:
        column = User.uid if model is User else getattr(model, "owner_uid")
        rows = db.scalars(
            select(model).where(column == uid).limit(_MAX_PER_TABLE + 1)
        ).all()
        if len(rows) > _MAX_PER_TABLE:
            raise HTTPException(
                413, f"Too many {name} records for direct download; request an assisted export"
            )
        export[name] = [
            {field.name: jsonable_encoder(getattr(row, field.name)) for field in model.__table__.columns}
            for row in rows
        ]

    response.headers["Cache-Control"] = "private, no-store, max-age=0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return {
        "format_version": 1,
        "source": "ChronoMind V2 PostgreSQL",
        "owner_uid": uid,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Firestore V1 data must be exported separately before cutover.",
            "LangGraph checkpoint internals are not included in this export.",
            "This operation only reads records; it does not delete an account.",
        ],
        "data": export,
    }
