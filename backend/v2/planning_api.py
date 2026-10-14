"""Read-only planning preview backed by PostgreSQL. Does not commit calendar changes."""
from collections import defaultdict
from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_session
from .models import FixedEvent, Preference, ScheduleBlock, Task
from .planner import BusyInterval, PlanningPreferences, PlanningTask, preview_schedule

router = APIRouter(prefix="/api/v2/planning", tags=["v2-planning"])


def _aware(instant: datetime | None) -> datetime | None:
    if instant is not None and (instant.tzinfo is None or instant.utcoffset() is None):
        # SQLite test adapters lose tzinfo; production PostgreSQL TIMESTAMPTZ is aware.
        return instant.replace(tzinfo=timezone.utc)
    return instant


@router.get("/preview")
def get_preview(
    days: int = Query(7, ge=1, le=14),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    pref = db.get(Preference, uid)
    if pref is None:
        # Read-only preview never provisions a database user or changes preferences.
        opts = PlanningPreferences("Asia/Kolkata", time(8), time(22), 480, 10)
    else:
        opts = PlanningPreferences(pref.timezone, pref.work_start, pref.work_end, pref.max_daily_minutes, pref.min_break_minutes)

    rows = db.scalars(select(Task).where(Task.owner_uid == uid, Task.status == "pending")).all()
    blocks = db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid)).all()
    events = db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == uid)).all()

    scheduled = defaultdict(int)
    occupied = []
    for block in blocks:
        start = _aware(block.starts_at)
        end = _aware(block.ends_at)
        scheduled[block.task_id] += int((end - start).total_seconds() // 60)
        occupied.append(BusyInterval(start, end, counts_as_work=True))
    for event in events:
        occupied.append(BusyInterval(_aware(event.starts_at), _aware(event.ends_at)))

    tasks = [
        PlanningTask(row.id, row.title, max(0, row.duration_minutes - scheduled[row.id]), row.importance, _aware(row.deadline_at))
        for row in rows
    ]
    generated = datetime.now(timezone.utc)
    suggestion = preview_schedule(tasks, occupied, opts, generated, horizon_days=days)
    return {
        "generated_at": generated.isoformat(),
        "timezone": opts.timezone,
        "changes_committed": False,
        "blocks": [
            {
                "task_id": block.task_id,
                "title": block.title,
                "starts_at": block.starts_at.astimezone(timezone.utc).isoformat(),
                "ends_at": block.ends_at.astimezone(timezone.utc).isoformat(),
                "duration_minutes": block.duration_minutes,
            }
            for block in suggestion.blocks
        ],
        "unscheduled": [
            {
                "task_id": task.task_id,
                "title": task.title,
                "remaining_minutes": task.remaining_minutes,
                "reason": task.reason,
            }
            for task in suggestion.unscheduled
        ],
    }
