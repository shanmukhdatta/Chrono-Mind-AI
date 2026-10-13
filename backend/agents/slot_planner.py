"""Deterministic, non-overlapping legacy rollover slot selection.

The returned placements are proposals only. Database writes must independently
recheck conflicts because concurrent user edits can happen after planning.
"""
from copy import deepcopy
from datetime import date, timedelta


def to_minutes(value: str) -> int:
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        raise ValueError("Expected HH:MM time")
    hours, minutes = int(value[:2]), int(value[3:])
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError("Invalid HH:MM time")
    return hours * 60 + minutes


def to_clock(minutes: int) -> str:
    if not (0 <= minutes <= 24 * 60):
        raise ValueError("Minutes outside day")
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def free_intervals(tasks, start=8 * 60, end=22 * 60):
    """Return free intervals after combining overlapping existing reservations."""
    occupied = []
    for task in tasks:
        begin = to_minutes(task["start_time"])
        finish = to_minutes(task["end_time"])
        if finish <= begin:
            raise ValueError("Invalid existing task duration")
        if finish > start and begin < end:
            occupied.append((max(start, begin), min(end, finish)))

    occupied.sort()
    free = []
    cursor = start
    for begin, finish in occupied:
        if begin > cursor:
            free.append((cursor, begin))
        cursor = max(cursor, finish)
    if cursor < end:
        free.append((cursor, end))
    return free


def plan_rollover(tasks, first_date: str, load_existing, horizon_days: int = 7):
    """Plan up to seven consecutive days, reserving slots as each task is placed.

    load_existing(iso_date) returns that date's task dictionaries. The callback
    is invoked only once per date; reservations are cached across all candidates.
    Never mutates input tasks or stored existing-task dictionaries.
    """
    if not 1 <= horizon_days <= 30:
        raise ValueError("horizon_days must be between 1 and 30")
    first = date.fromisoformat(first_date)
    cache = {}
    planned, unplaced = [], []
    for original in tasks:
        try:
            needed = int(original["duration_minutes"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Task has invalid duration_minutes") from exc
        if needed < 15 or needed > 24 * 60:
            raise ValueError("Task duration outside supported bounds")
        found = False
        for offset in range(horizon_days):
            target = (first + timedelta(days=offset)).isoformat()
            if target not in cache:
                cache[target] = [dict(t) for t in load_existing(target)]
            for begin, end in free_intervals(cache[target]):
                if end - begin < needed:
                    continue
                item = deepcopy(original)
                item.update(
                    date=target,
                    start_time=to_clock(begin),
                    end_time=to_clock(begin + needed),
                    rescheduled=True,
                    rescheduled_from=original["date"],
                )
                planned.append(item)
                # Reserve proposed placement for subsequent tasks immediately.
                cache[target].append(
                    {"start_time": item["start_time"], "end_time": item["end_time"]}
                )
                found = True
                break
            if found:
                break
        if not found:
            unplaced.append(original.get("task_id"))
    return planned, unplaced
