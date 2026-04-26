"""
ChronoMind AI — Scheduler Service
Free slot detection, conflict resolution, task placement
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.models import Task, TimetableEntry, TaskStatus


def time_to_minutes(t: str) -> int:
    """Convert HH:MM to minutes since midnight."""
    h, m = map(int, t.split(":"))
    return h * 60 + m


def minutes_to_time(m: int) -> str:
    """Convert minutes since midnight to HH:MM."""
    return f"{m // 60:02d}:{m % 60:02d}"


def get_day_name(d: date) -> str:
    return d.strftime("%A")  # Monday, Tuesday, etc.


async def get_busy_slots(
    db: AsyncSession,
    user_id: str,
    target_date: date,
) -> List[Dict[str, int]]:
    """Return all busy time ranges (in minutes) for a given date."""
    day_name = get_day_name(target_date)
    date_str = target_date.isoformat()
    busy = []

    # Timetable entries (recurring)
    tt_result = await db.execute(
        select(TimetableEntry).where(
            and_(
                TimetableEntry.user_id == user_id,
                TimetableEntry.day_of_week == day_name,
                TimetableEntry.is_recurring == True,
            )
        )
    )
    for entry in tt_result.scalars():
        busy.append({
            "start": time_to_minutes(entry.start_time),
            "end": time_to_minutes(entry.end_time),
            "label": entry.subject,
            "type": "class",
        })

    # Existing tasks on this date
    task_result = await db.execute(
        select(Task).where(
            and_(
                Task.user_id == user_id,
                Task.scheduled_date == date_str,
                Task.status.notin_([TaskStatus.CANCELLED]),
                Task.start_time.isnot(None),
            )
        )
    )
    for task in task_result.scalars():
        busy.append({
            "start": time_to_minutes(task.start_time),
            "end": time_to_minutes(task.end_time),
            "label": task.title,
            "type": "task",
        })

    # Sort by start time
    return sorted(busy, key=lambda x: x["start"])


async def find_free_slots(
    db: AsyncSession,
    user_id: str,
    target_date: date,
    duration_minutes: int,
    preferred_start: int = 8 * 60,   # 8 AM
    preferred_end: int = 22 * 60,    # 10 PM
) -> List[Dict[str, str]]:
    """Find all free slots of at least `duration_minutes` on a given date."""
    busy = await get_busy_slots(db, user_id, target_date)

    free_slots = []
    current = preferred_start

    for block in busy:
        block_start = max(block["start"], preferred_start)
        block_end = min(block["end"], preferred_end)

        if current + duration_minutes <= block_start:
            free_slots.append({
                "start": minutes_to_time(current),
                "end": minutes_to_time(block_start),
                "duration_minutes": block_start - current,
            })
        current = max(current, block_end)

    # Check slot after last block
    if current + duration_minutes <= preferred_end:
        free_slots.append({
            "start": minutes_to_time(current),
            "end": minutes_to_time(preferred_end),
            "duration_minutes": preferred_end - current,
        })

    # Filter out slots shorter than requested duration
    return [s for s in free_slots if s["duration_minutes"] >= duration_minutes]


async def find_best_slot(
    db: AsyncSession,
    user_id: str,
    duration_minutes: int,
    deadline: Optional[datetime] = None,
    preferred_start: int = 8 * 60,
    preferred_end: int = 22 * 60,
    chronotype: str = "flexible",
    start_from: Optional[date] = None,
) -> Optional[Tuple[date, str, str]]:
    """
    Find the best (date, start_time, end_time) for a task.
    Tries today, then tomorrow, up to 7 days ahead.
    Returns None if no slot found.
    """
    today = start_from or date.today()

    # Adjust preferred window based on chronotype
    if chronotype == "morning":
        preferred_start = max(preferred_start, 6 * 60)
        preferred_end = min(preferred_end, 13 * 60)
    elif chronotype == "night":
        preferred_start = max(preferred_start, 14 * 60)
        preferred_end = min(preferred_end, 23 * 60)

    # Determine deadline limit
    deadline_date = deadline.date() if deadline else today + timedelta(days=7)
    days_to_check = min((deadline_date - today).days + 1, 7)

    for i in range(days_to_check):
        target_date = today + timedelta(days=i)
        slots = await find_free_slots(
            db, user_id, target_date, duration_minutes, preferred_start, preferred_end
        )
        if slots:
            # Pick best slot (first one that fits cleanly)
            best = slots[0]
            start_min = time_to_minutes(best["start"])
            end_min = start_min + duration_minutes
            return (
                target_date,
                minutes_to_time(start_min),
                minutes_to_time(end_min),
            )

    return None


async def has_conflict(
    db: AsyncSession,
    user_id: str,
    target_date: date,
    start_time: str,
    end_time: str,
    exclude_task_id: Optional[str] = None,
) -> bool:
    """Check if placing a task at this slot conflicts with existing entries."""
    busy = await get_busy_slots(db, user_id, target_date)
    new_start = time_to_minutes(start_time)
    new_end = time_to_minutes(end_time)

    for block in busy:
        if block.get("id") == exclude_task_id:
            continue
        # Overlap if not (new_end <= block_start or new_start >= block_end)
        if not (new_end <= block["start"] or new_start >= block["end"]):
            return True
    return False


async def get_week_stats(db: AsyncSession, user_id: str) -> Dict:
    """Compute dashboard stats for the current week."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # Total slots found this week (count free slot opportunities)
    slots_found = 0
    for i in range(7):
        d = week_start + timedelta(days=i)
        slots = await find_free_slots(db, user_id, d, 30)
        slots_found += len(slots)

    # AI-placed tasks this week
    task_result = await db.execute(
        select(Task).where(
            and_(
                Task.user_id == user_id,
                Task.ai_placed == True,
                Task.scheduled_date >= week_start.isoformat(),
                Task.scheduled_date <= week_end.isoformat(),
            )
        )
    )
    ai_tasks = task_result.scalars().all()

    # Completion rate
    all_tasks_result = await db.execute(
        select(Task).where(
            and_(
                Task.user_id == user_id,
                Task.scheduled_date >= week_start.isoformat(),
                Task.scheduled_date <= week_end.isoformat(),
            )
        )
    )
    all_tasks = all_tasks_result.scalars().all()
    completed = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
    completion_rate = (len(completed) / len(all_tasks) * 100) if all_tasks else 0

    # Today's tasks
    today_str = today.isoformat()
    today_tasks_result = await db.execute(
        select(Task).where(
            and_(Task.user_id == user_id, Task.scheduled_date == today_str)
        )
    )
    today_tasks = today_tasks_result.scalars().all()

    return {
        "slots_found_this_week": slots_found,
        "tasks_ai_scheduled": len(ai_tasks),
        "completion_rate": round(completion_rate, 1),
        "tasks_today": len(today_tasks),
        "tasks_pending": len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
        "tasks_completed": len(completed),
        "streak_days": 3,  # TODO: implement streak tracking
    }
