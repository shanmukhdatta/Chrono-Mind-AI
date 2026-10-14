"""Bounded recurrence generation with per-date exceptions and idempotent lineage."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_or_create_user, get_session
from .models import (
    RecurrenceOccurrence, RecurrenceSeries, RecurrenceSkip,
    ScheduleBlock, Task, User,
)

router = APIRouter(prefix="/api/v2/recurrence", tags=["v2-recurrence"])


class SeriesInput(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    duration_minutes: int = Field(ge=1, le=1440)
    importance: str = "important"
    frequency: str
    weekdays: list[int] = Field(default_factory=list)
    timezone: str = "Asia/Kolkata"
    due_time: time | None = None
    start_date: date
    end_date: date | None = None

    @field_validator("timezone")
    @classmethod
    def check_zone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value

    @model_validator(mode="after")
    def validate(self):
        if not self.title.strip():
            raise ValueError("Title cannot be blank")
        self.title = self.title.strip()
        if self.importance not in ("important", "not_important"):
            raise ValueError("Unsupported importance")
        if self.frequency not in ("daily", "weekly", "monthly"):
            raise ValueError("Frequency must be daily, weekly, or monthly")
        if self.frequency == "weekly" and (not self.weekdays or len(set(self.weekdays)) != len(self.weekdays)
                or any(not 0 <= day <= 6 for day in self.weekdays)):
            raise ValueError("Weekly recurrence requires unique weekdays 0=Mon..6=Sun")
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("End date precedes start date")
        if self.frequency in ("daily", "monthly") and self.weekdays:
            raise ValueError("Daily and monthly recurrence must not include weekdays")
        return self


class SkipInput(BaseModel):
    occurrence_date: date


def owned(db: Session, uid: str, series_id: str):
    series = db.scalar(select(RecurrenceSeries).where(
        RecurrenceSeries.id == series_id, RecurrenceSeries.owner_uid == uid
    ).with_for_update())
    if series is None:
        raise HTTPException(404, "Recurrence series not found")
    return series


def due_instant(day: date, due_time: time, zone_name: str) -> datetime:
    zone = ZoneInfo(zone_name)
    local = datetime.combine(day, due_time, zone)
    # Refuse ambiguous/nonexistent DST wall times instead of silently shifting them.
    alternate = local.replace(fold=1)
    if alternate.utcoffset() != local.utcoffset():
        raise ValueError("Ambiguous local due time due to daylight saving")
    restored = local.astimezone(timezone.utc).astimezone(zone)
    if restored.date() != day or restored.timetz().replace(tzinfo=None) != due_time:
        raise ValueError("Nonexistent local due time due to daylight saving")
    return local.astimezone(timezone.utc)


def upcoming_dates(series: RecurrenceSeries, today: date, days: int):
    if not 1 <= days <= 90:
        raise ValueError("Days must be 1..90")
    start = max(today, series.start_date)
    for offset in range(days):
        current = start + timedelta(days=offset)
        if series.end_date and current > series.end_date:
            break
        if series.frequency == "daily":
            yield current
        elif series.frequency == "weekly":
            if current.weekday() in {int(n) for n in series.weekdays.split(",") if n}:
                yield current
        elif series.frequency == "monthly":
            if current.day == series.start_date.day:
                yield current


@router.get("")
def list_series(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    rows = db.scalars(select(RecurrenceSeries).where(
        RecurrenceSeries.owner_uid == user["uid"]
    ).order_by(RecurrenceSeries.start_date)).all()
    return [
        {"id": row.id, "title": row.title, "duration_minutes": row.duration_minutes,
         "importance": row.importance, "frequency": row.frequency,
         "weekdays": [int(n) for n in row.weekdays.split(",") if n],
         "timezone": row.timezone,
         "start_date": row.start_date.isoformat(),
         "end_date": row.end_date.isoformat() if row.end_date else None,
         "due_time": row.due_time.isoformat() if row.due_time else None,
         "active": row.active}
        for row in rows
    ]


@router.post("", status_code=201)
def create_series(body: SeriesInput, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    get_or_create_user(db, uid)
    row = RecurrenceSeries(
        owner_uid=uid, title=body.title,
        duration_minutes=body.duration_minutes,
        importance=body.importance, frequency=body.frequency,
        weekdays=",".join(str(x) for x in sorted(body.weekdays)),
        timezone=body.timezone, due_time=body.due_time,
        start_date=body.start_date, end_date=body.end_date,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "active": row.active, "frequency": row.frequency, "title": row.title}


@router.post("/{series_id}/pause")
def pause_series(series_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    row = owned(db, user["uid"], series_id)
    row.active = False
    row.version += 1
    db.commit()
    return {"id": row.id, "active": row.active, "note": "Existing tasks are not deleted"}


@router.post("/{series_id}/resume")
def resume_series(series_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    row = owned(db, user["uid"], series_id)
    row.active = True
    row.version += 1
    db.commit()
    return {"id": row.id, "active": row.active}


def materialize_series_occurrences(db: Session, uid: str, series: RecurrenceSeries, days: int = 30) -> tuple[int, int, int]:
    """Materialize missing occurrences for a series within a horizon. Caller commits transaction."""
    if not series.active:
        return 0, 0, 0
    today = datetime.now(ZoneInfo(series.timezone)).date()
    existing = {
        row.occurrence_date for row in db.scalars(select(RecurrenceOccurrence).where(
            RecurrenceOccurrence.series_id == series.id, RecurrenceOccurrence.owner_uid == uid
        )).all()
    }
    skipped = {
        row.occurrence_date for row in db.scalars(select(RecurrenceSkip).where(
            RecurrenceSkip.series_id == series.id, RecurrenceSkip.owner_uid == uid
        )).all()
    }
    pending = [day for day in upcoming_dates(series, today, days) if day not in existing and day not in skipped]
    due_dates = {}
    for day in pending:
        due_dates[day] = due_instant(day, series.due_time, series.timezone) if series.due_time else None

    for day in pending:
        task = Task(
            owner_uid=uid,
            title=series.title,
            duration_minutes=series.duration_minutes,
            importance=series.importance,
            recurrence_rule="series:" + series.id,
            deadline_at=due_dates[day],
        )
        db.add(task)
        db.flush()
        db.add(RecurrenceOccurrence(
            owner_uid=uid, series_id=series.id,
            occurrence_date=day, task_id=task.id,
        ))
    return len(pending), len(existing), len(skipped)


@router.post("/{series_id}/materialize")
def materialize_series(
    series_id: str, days: int = Query(30, ge=1, le=90),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    db.scalar(select(User).where(User.uid == uid).with_for_update())
    series = owned(db, uid, series_id)
    if not series.active:
        raise HTTPException(409, "Recurrence series is paused")
    try:
        created, existing_count, skipped_count = materialize_series_occurrences(db, uid, series, days)
        db.commit()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"series_id": series.id, "created": created, "already_present": existing_count, "skipped": skipped_count}


@router.post("/{series_id}/skip")
def skip_occurrence(
    series_id: str, body: SkipInput,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    db.scalar(select(User).where(User.uid == uid).with_for_update())
    series = owned(db, uid, series_id)
    occurrence_day = body.occurrence_date
    if occurrence_day < datetime.now(ZoneInfo(series.timezone)).date():
        raise HTTPException(409, "Past occurrences cannot be skipped")
    if occurrence_day < series.start_date or (series.end_date and occurrence_day > series.end_date):
        raise HTTPException(422, "Date is outside this recurrence")
    row = db.scalar(select(RecurrenceSkip).where(
        RecurrenceSkip.owner_uid == uid, RecurrenceSkip.series_id == series.id,
        RecurrenceSkip.occurrence_date == occurrence_day
    ))
    if row is not None:
        return {"skipped": True, "already_skipped": True}
    occurrence = db.scalar(select(RecurrenceOccurrence).where(
        RecurrenceOccurrence.owner_uid == uid, RecurrenceOccurrence.series_id == series.id,
        RecurrenceOccurrence.occurrence_date == occurrence_day
    ))
    if occurrence is not None:
        task = db.scalar(select(Task).where(Task.id == occurrence.task_id, Task.owner_uid == uid))
        if task is None or task.status != "pending":
            raise HTTPException(409, "Completed or missing occurrences cannot be skipped")
        linked = db.scalar(select(ScheduleBlock.id).where(
            ScheduleBlock.owner_uid == uid, ScheduleBlock.task_id == task.id
        ).limit(1))
        if linked is not None:
            raise HTTPException(409, "Remove scheduled sessions before skipping this occurrence")
        task.status = "archived"
        task.version += 1
    db.add(RecurrenceSkip(owner_uid=uid, series_id=series.id, occurrence_date=occurrence_day))
    db.commit()
    return {"skipped": True, "already_skipped": False}
