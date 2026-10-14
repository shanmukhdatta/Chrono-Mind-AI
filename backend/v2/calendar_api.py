"""Real PostgreSQL fixed commitments and read-only unified V2 calendar endpoints."""
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_or_create_user, get_session
from .models import FixedEvent, ScheduleBlock, Task, User

router = APIRouter(prefix="/api/v2", tags=["v2-calendar"])


class EventInput(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Use an explicit timezone offset")
        return value

    @field_validator("title")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Event title cannot be blank")
        return value.strip()

    @model_validator(mode="after")
    def check_order(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("Event end must follow start")
        if self.ends_at - self.starts_at > timedelta(days=7):
            raise ValueError("Fixed events may span at most 7 days")
        return self


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    starts_at: datetime
    ends_at: datetime


def lock_owner(db: Session, uid: str):
    get_or_create_user(db, uid)
    # PostgreSQL row-level owner lock serializes conflict-checked calendar edits.
    db.scalar(select(User).where(User.uid == uid).with_for_update())


def conflict(db: Session, uid: str, start: datetime, end: datetime, exclude_event: str | None = None) -> bool:
    events = select(FixedEvent.id).where(
        FixedEvent.owner_uid == uid, FixedEvent.starts_at < end, FixedEvent.ends_at > start
    )
    if exclude_event:
        events = events.where(FixedEvent.id != exclude_event)
    if db.scalar(events.limit(1)) is not None:
        return True
    blocks = select(ScheduleBlock.id).where(
        ScheduleBlock.owner_uid == uid, ScheduleBlock.starts_at < end, ScheduleBlock.ends_at > start
    )
    return db.scalar(blocks.limit(1)) is not None


@router.get("/fixed-events", response_model=list[EventOut])
def list_events(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    return db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == user["uid"]).order_by(FixedEvent.starts_at)).all()


@router.post("/fixed-events", response_model=EventOut, status_code=201)
def create_event(body: EventInput, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    lock_owner(db, uid)
    if conflict(db, uid, body.starts_at, body.ends_at):
        raise HTTPException(409, "This interval overlaps a fixed event or scheduled task")
    row = FixedEvent(owner_uid=uid, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/fixed-events/{event_id}", response_model=EventOut)
def update_event(event_id: str, body: EventInput, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    lock_owner(db, uid)
    row = db.scalar(select(FixedEvent).where(FixedEvent.id == event_id, FixedEvent.owner_uid == uid))
    if row is None:
        raise HTTPException(404, "Not found")
    if conflict(db, uid, body.starts_at, body.ends_at, exclude_event=event_id):
        raise HTTPException(409, "This interval overlaps a fixed event or scheduled task")
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/fixed-events/{event_id}", status_code=204)
def delete_event(event_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    lock_owner(db, uid)
    row = db.scalar(select(FixedEvent).where(FixedEvent.id == event_id, FixedEvent.owner_uid == uid))
    if row is None:
        raise HTTPException(404, "Not found")
    db.delete(row)
    db.commit()


@router.get("/calendar")
def calendar_range(
    starts_at: Annotated[datetime, Query()],
    ends_at: Annotated[datetime, Query()],
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    for instant in (starts_at, ends_at):
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise HTTPException(422, "Explicit timezone offsets required")
    if ends_at <= starts_at or ends_at - starts_at > timedelta(days=31):
        raise HTTPException(422, "Date window must be positive and no longer than 31 days")
    uid = user["uid"]
    fixed = db.scalars(select(FixedEvent).where(
        FixedEvent.owner_uid == uid, FixedEvent.starts_at < ends_at, FixedEvent.ends_at > starts_at
    ).order_by(FixedEvent.starts_at)).all()
    blocks = db.scalars(select(ScheduleBlock).where(
        ScheduleBlock.owner_uid == uid, ScheduleBlock.starts_at < ends_at, ScheduleBlock.ends_at > starts_at
    ).order_by(ScheduleBlock.starts_at)).all()
    task_ids = {block.task_id for block in blocks}
    titles = {}
    if task_ids:
        titles = dict(db.execute(select(Task.id, Task.title).where(Task.owner_uid == uid, Task.id.in_(task_ids))).all())
    return {
        "fixed_events": [{"id": row.id, "title": row.title, "starts_at": row.starts_at, "ends_at": row.ends_at}
                         for row in fixed],
        "task_blocks": [{"id": row.id, "task_id": row.task_id, "title": titles.get(row.task_id, "Task"),
                         "starts_at": row.starts_at, "ends_at": row.ends_at}
                        for row in blocks],
    }
