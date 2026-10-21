"""Authenticated PostgreSQL-backed dashboard and score explainability."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_session
from .models import Goal, Preference, ScheduleBlock, Task
from .priority import context_matches, score_task

router = APIRouter(prefix="/api/v2/dashboard", tags=["v2-dashboard"])


def aware(value: datetime | None):
    if value and (value.tzinfo is None or value.utcoffset() is None):
        return value.replace(tzinfo=timezone.utc)
    return value


@router.get("")
def dashboard(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    pref = db.get(Preference, uid)
    timezone_name = pref.timezone if pref else "Asia/Kolkata"
    zone = ZoneInfo(timezone_name)
    now = datetime.now(timezone.utc)
    today = now.astimezone(zone).date()
    tasks = db.scalars(select(Task).where(Task.owner_uid == uid)).all()
    goals = db.scalars(select(Goal).where(Goal.owner_uid == uid)).all()
    active_ids = {goal.id for goal in goals if goal.status == "active"}
    pending = [task for task in tasks if task.status == "pending"]
    completed = [task for task in tasks if task.status == "completed"]
    # Past sessions for still-pending work are recorded postponements.
    postponed = {}
    for block in db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid)).all():
        if aware(block.ends_at) <= now:
            postponed[block.task_id] = postponed.get(block.task_id, 0) + 1
    focus_context = pref.focus_context if pref else None
    scored = []
    for task in pending:
        deadline = aware(task.deadline_at)
        signal = score_task(
            task.importance, deadline, task.goal_id in active_ids, now,
            postponements=postponed.get(task.id, 0),
            context_match=context_matches(focus_context, task.context_tags),
            splittable=task.splittable,
            duration_minutes=task.duration_minutes,
        )
        scored.append({
            "id": task.id,
            "title": task.title,
            "importance": task.importance,
            "deadline_at": deadline.isoformat() if deadline else None,
            "duration_minutes": task.duration_minutes,
            "goal_id": task.goal_id,
            "priority_score": signal.score,
            "priority_reasons": list(signal.reasons),
            "context_tags": list(task.context_tags or []),
            "postponements": postponed.get(task.id, 0),
        })
    scored.sort(key=lambda t: (-t["priority_score"], t["deadline_at"] or "9999", t["id"]))
    last_week = [
        {"date": (today - timedelta(days=offset)).isoformat(), "completed": 0}
        for offset in range(6, -1, -1)
    ]
    day_counts = {entry["date"]: entry for entry in last_week}
    for task in completed:
        when = aware(task.completed_at)
        if when:
            key = when.astimezone(zone).date().isoformat()
            if key in day_counts:
                day_counts[key]["completed"] += 1

    blocks = db.scalars(select(ScheduleBlock).where(ScheduleBlock.owner_uid == uid)).all()
    today_minutes = 0
    for block in blocks:
        start = aware(block.starts_at)
        end = aware(block.ends_at)
        local_start = start.astimezone(zone)
        local_end = end.astimezone(zone)
        if local_start.date() == today and local_end.date() == today:
            today_minutes += int((end - start).total_seconds() // 60)

    overdue = sum(bool(task.deadline_at and aware(task.deadline_at) < now) for task in pending)
    return {
        "today": today.isoformat(),
        "timezone": timezone_name,
        "pending_count": len(pending),
        "completed_count": len(completed),
        "archived_count": sum(task.status == "archived" for task in tasks),
        "active_goals": len(active_ids),
        "overdue_count": overdue,
        "scheduled_minutes_today": today_minutes,
        "completion_rate": round(len(completed) / max(1, len(pending) + len(completed)) * 100, 1),
        "top_priorities": scored[:10],
        "completed_last_seven_days": last_week,
        "focus_context": focus_context,
        "scoring": {
            "base": 15, "important_bonus": 35, "active_goal_bonus": 15,
            "overdue_bonus": 40, "due_24h_bonus": 30,
            "due_72h_bonus": 20, "due_week_bonus": 10,
            "postponement_bonus_per_event": 5, "postponement_bonus_cap": 15,
            "context_match_bonus": 15, "unsplittable_bonus": 5,
            "score_cap": 100,
        },
        "source": "database",
    }
