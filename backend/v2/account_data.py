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
    AssistantMetric, Goal, InAppNotification, LegacyTaskArchive, PlanProposal, PlanningDecisionLog, Preference,
    RecurrenceOccurrence, RecurrenceSeries, RecurrenceSkip, ScheduleBlock, Task, TaskDependency, User,
)

router = APIRouter(prefix="/api/v2/account", tags=["v2-account"])

_EXPORT_TABLES = (
    ("users", User), ("goals", Goal), ("tasks", Task),
    ("schedule_blocks", ScheduleBlock), ("task_dependencies", TaskDependency), ("fixed_events", FixedEvent),
    ("preferences", Preference), ("planning_proposals", PlanProposal),
    ("planning_decisions", PlanningDecisionLog), ("assistant_metrics", AssistantMetric),
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


@router.delete("", status_code=200)
def delete_user_account_data(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Safely and permanently purge all V2 PostgreSQL records and legacy collections for this user."""
    from sqlalchemy import delete
    uid = user["uid"]

    # Lock user row if present
    db.scalar(select(User).where(User.uid == uid).with_for_update())

    # Reverse dependency deletion order
    deletion_order = (
        InAppNotification,
        BehaviorEvent,
        BehaviorConsent,
        FocusSession,
        RecurrenceSkip,
        RecurrenceOccurrence,
        RecurrenceSeries,
        PlanningDecisionLog,
        AssistantMetric,
        PlanProposal,
        ScheduleBlock,
        TaskDependency,
        Task,
        Goal,
        FixedEvent,
        Preference,
        LegacyTaskArchive,
        User,
    )

    deleted_counts = {}
    for model in deletion_order:
        column = User.uid if model is User else getattr(model, "owner_uid")
        result = db.execute(delete(model).where(column == uid))
        deleted_counts[model.__tablename__] = result.rowcount

    # Also clean up legacy Firestore tasks and notifications if initialized
    firestore_cleaned = False
    try:
        from services.firebase_service import get_db
        fdb = get_db()
        if fdb is not None:
            user_ref = fdb.collection("users").document(uid)
            for coll in ("tasks", "notifications"):
                docs = list(user_ref.collection(coll).stream())
                if docs:
                    batch = fdb.batch()
                    for d in docs:
                        batch.delete(d.reference)
                    batch.commit()
            firestore_cleaned = True
    except Exception:
        # Firestore may not be initialized or configured in this test environment
        pass

    db.commit()
    return {
        "deleted": True,
        "uid": uid,
        "records_purged": deleted_counts,
        "firestore_cleaned": firestore_cleaned,
    }

