"""Explicit, non-destructive Firestore V1 -> PostgreSQL V2 backfill helpers.

Never modifies Firestore or automatically runs on app startup.
"""
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_or_create_user
from .models import FixedEvent, LegacyTaskArchive, ScheduleBlock, Task


@dataclass(frozen=True)
class Conversion:
    owner_uid: str
    legacy_id: str
    task_data: dict
    starts_at: datetime
    ends_at: datetime
    raw_json: str
    source_hash: str


def convert_legacy_task(
    owner_uid: str, legacy_id: str, record: dict, timezone_name: str
) -> Conversion:
    """Convert a scheduled V1 event without reinterpreting its end as a deadline."""
    if not owner_uid.strip() or not legacy_id.strip():
        raise ValueError("Owner UID and document ID are required")
    zone = ZoneInfo(timezone_name)
    title = record.get("title")
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 160:
        raise ValueError("Malformed task title")
    legacy_date = date.fromisoformat(record["date"])
    starts = time.fromisoformat(record["start_time"])
    ends = time.fromisoformat(record["end_time"])
    if ends <= starts:
        raise ValueError("Unordered legacy time range")
    start_local = datetime.combine(legacy_date, starts, zone)
    end_local = datetime.combine(legacy_date, ends, zone)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    if end_utc <= start_utc:
        raise ValueError("Invalid timezone transition")
    mins = int((end_utc - start_utc).total_seconds() // 60)
    if not 1 <= mins <= 1440:
        raise ValueError("Unsupported legacy session duration")
    is_complete = bool(record.get("completed", False))
    timestamp = record.get("completed_at")
    completed_at = None
    if is_complete:
        if isinstance(timestamp, datetime) and timestamp.tzinfo:
            completed_at = timestamp.astimezone(timezone.utc)
        else:
            completed_at = end_utc
    importance = "not_important" if record.get("importance") == "not_important" else "important"
    raw = json.dumps(record, sort_keys=True, default=str, ensure_ascii=False)
    return Conversion(
        owner_uid=owner_uid, legacy_id=legacy_id,
        task_data={
            "owner_uid": owner_uid, "legacy_id": legacy_id,
            "title": title.strip(),
            "duration_minutes": mins,
            "importance": importance,
            "status": "completed" if is_complete else "pending",
            "completed_at": completed_at,
            "description": "",
            "deadline_at": None,  # V1 end-of-session is not a deadline.
        },
        starts_at=start_utc, ends_at=end_utc, raw_json=raw,
        source_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    )


def has_calendar_collision(db: Session, uid: str, start: datetime, end: datetime) -> bool:
    fixed = select(FixedEvent.id).where(
        FixedEvent.owner_uid == uid, FixedEvent.starts_at < end, FixedEvent.ends_at > start
    )
    scheduled = select(ScheduleBlock.id).where(
        ScheduleBlock.owner_uid == uid, ScheduleBlock.starts_at < end, ScheduleBlock.ends_at > start
    )
    return db.scalar(fixed.limit(1)) is not None or db.scalar(scheduled.limit(1)) is not None


def import_converted(db: Session, item: Conversion) -> str:
    """Return imported / already_present / imported_unscheduled; caller owns transaction."""
    get_or_create_user(db, item.owner_uid)
    existing = db.scalar(select(Task).where(
        Task.owner_uid == item.owner_uid, Task.legacy_id == item.legacy_id
    ))
    if existing is not None:
        return "already_present"

    archive = LegacyTaskArchive(
        owner_uid=item.owner_uid, legacy_id=item.legacy_id,
        original_json=item.raw_json, source_hash=item.source_hash,
    )
    task = Task(**item.task_data)
    db.add(task)
    db.add(archive)
    db.flush()
    if has_calendar_collision(db, item.owner_uid, item.starts_at, item.ends_at):
        return "imported_unscheduled"
    db.add(ScheduleBlock(
        owner_uid=item.owner_uid, task_id=task.id,
        starts_at=item.starts_at, ends_at=item.ends_at, source="legacy_firestore",
    ))
    return "imported"
