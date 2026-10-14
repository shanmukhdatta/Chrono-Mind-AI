"""Read-only planning preview backed by PostgreSQL. Does not commit calendar changes."""
from collections import defaultdict
from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_session
from .models import BehaviorConsent, BehaviorEvent, FixedEvent, Goal, Preference, ScheduleBlock, Task, TaskDependency
from .priority import score_task
from .personalization import preferred_work_hour
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
    consent = db.get(BehaviorConsent, uid)
    preferred = None
    if consent is not None and consent.enabled:
        signals = db.scalars(select(BehaviorEvent).where(
            BehaviorEvent.owner_uid == uid, BehaviorEvent.kind == "focus_completed"
        ).order_by(BehaviorEvent.happened_at.desc()).limit(90)).all()
        preferred = preferred_work_hour(
            [(event.hour_of_day, event.duration_seconds) for event in signals]
        )
    pref = db.get(Preference, uid)
    if pref is None:
        # Read-only preview never provisions a database user or changes preferences.
        opts = PlanningPreferences("Asia/Kolkata", time(8), time(22), 480, 10, preferred)
    else:
        opts = PlanningPreferences(
            pref.timezone, pref.work_start, pref.work_end,
            pref.max_daily_minutes, pref.min_break_minutes, preferred
        )

    rows = db.scalars(select(Task).where(Task.owner_uid == uid, Task.status == "pending")).all()
    blocks = db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid)).all()
    events = db.scalars(select(FixedEvent).where(FixedEvent.owner_uid == uid)).all()

    dependencies = db.scalars(select(TaskDependency).where(TaskDependency.owner_uid == uid)).all()
    prerequisite_ids = {item.depends_on_id for item in dependencies}
    known = {
        task.id: task.status for task in db.scalars(select(Task).where(
            Task.owner_uid == uid, Task.id.in_(prerequisite_ids)
        )).all()
    } if prerequisite_ids else {}
    blockers = defaultdict(list)
    for dependency in dependencies:
        if known.get(dependency.depends_on_id) != "completed":
            blockers[dependency.task_id].append(dependency.depends_on_id)

    scheduled = defaultdict(int)
    occupied = []
    for block in blocks:
        start = _aware(block.starts_at)
        end = _aware(block.ends_at)
        scheduled[block.task_id] += int((end - start).total_seconds() // 60)
        occupied.append(BusyInterval(start, end, counts_as_work=True))
    for event in events:
        occupied.append(BusyInterval(_aware(event.starts_at), _aware(event.ends_at)))

    active_goal_ids = set(db.scalars(select(Goal.id).where(
        Goal.owner_uid == uid, Goal.status == "active"
    )).all())
    generated = datetime.now(timezone.utc)
    tasks = [
        PlanningTask(
            row.id, row.title, max(0, row.duration_minutes - scheduled[row.id]),
            row.importance, _aware(row.deadline_at),
            ("Prerequisite tasks are not yet completed: " + ", ".join(sorted(blockers[row.id])))
            if blockers[row.id] else None,
            score_task(
                row.importance, _aware(row.deadline_at),
                row.goal_id in active_goal_ids, generated
            ).score,
        )
        for row in rows
    ]
    suggestion = preview_schedule(tasks, occupied, opts, generated, horizon_days=days)
    return {
        "generated_at": generated.isoformat(),
        "timezone": opts.timezone,
        "changes_committed": False,
        "personalization": {
            "applied": preferred is not None,
            "preferred_hour": preferred,
            "method": "opt-in focus-hour heuristic" if preferred is not None else "off or insufficient samples",
        },
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
