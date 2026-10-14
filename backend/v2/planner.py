"""Pure deterministic scheduling engine: no LLM calls and no database writes."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class PlanningTask:
    task_id: str
    title: str
    remaining_minutes: int
    importance: str = "important"
    deadline_at: datetime | None = None


@dataclass(frozen=True)
class BusyInterval:
    start: datetime
    end: datetime
    counts_as_work: bool = False


@dataclass(frozen=True)
class PlanningPreferences:
    timezone: str
    work_start: time
    work_end: time
    max_daily_minutes: int
    min_break_minutes: int


@dataclass(frozen=True)
class ProposedBlock:
    task_id: str
    title: str
    starts_at: datetime
    ends_at: datetime
    duration_minutes: int


@dataclass(frozen=True)
class UnscheduledTask:
    task_id: str
    title: str
    remaining_minutes: int
    reason: str


@dataclass(frozen=True)
class PlanPreview:
    blocks: tuple[ProposedBlock, ...]
    unscheduled: tuple[UnscheduledTask, ...]


def _check_instant(instant: datetime) -> None:
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("All instants must be timezone aware")


def _work_minutes(intervals: list[BusyInterval], start: datetime, end: datetime) -> int:
    """Measure task-work occupancy within a given local workday."""
    total = 0
    for item in intervals:
        if item.counts_as_work:
            overlap = max(0, (min(end, item.end) - max(start, item.start)).total_seconds())
            total += int(overlap // 60)
    return total


def _free_windows(start: datetime, end: datetime, occupied: list[BusyInterval]):
    """Return disjoint empty segments of [start, end) after unioning occupied intervals."""
    clipped = sorted(
        [(max(start, item.start), min(end, item.end))
         for item in occupied if item.end > start and item.start < end],
        key=lambda item: item[0],
    )
    cursor = start
    for low, high in clipped:
        if low > cursor:
            yield cursor, low
        if high > cursor:
            cursor = high
    if cursor < end:
        yield cursor, end


def preview_schedule(
    tasks: list[PlanningTask],
    existing: list[BusyInterval],
    preferences: PlanningPreferences,
    now: datetime,
    horizon_days: int = 7,
) -> PlanPreview:
    """Build a bounded, conflict-free suggestion; never mutate tasks or persisted calendar."""
    _check_instant(now)
    if not 1 <= horizon_days <= 14:
        raise ValueError("horizon_days must be 1..14")
    if preferences.work_start >= preferences.work_end:
        raise ValueError("Work window must end after it begins")
    if preferences.max_daily_minutes <= 0 or preferences.min_break_minutes < 0:
        raise ValueError("Invalid daily limits")
    zone = ZoneInfo(preferences.timezone)
    local_now = now.astimezone(zone)
    occupied = list(existing)
    for interval in occupied:
        _check_instant(interval.start)
        _check_instant(interval.end)
        if interval.end <= interval.start:
            raise ValueError("Busy interval must have positive duration")
    if preferences.min_break_minutes:
        occupied.extend(
            BusyInterval(item.end, item.end + timedelta(minutes=preferences.min_break_minutes))
            for item in existing if item.counts_as_work
        )
    blocks = []
    unscheduled = []

    ordered = sorted(tasks, key=lambda t: (
        0 if t.importance == "important" else 1,
        t.deadline_at or datetime.max.replace(tzinfo=zone),
        t.task_id,
    ))

    for task in ordered:
        remaining = task.remaining_minutes
        if remaining <= 0:
            continue
        if task.deadline_at is not None:
            _check_instant(task.deadline_at)
        for day_offset in range(horizon_days):
            if remaining <= 0:
                break
            day = local_now.date() + timedelta(days=day_offset)
            full_day_start = datetime.combine(day, preferences.work_start, zone)
            full_day_end = datetime.combine(day, preferences.work_end, zone)
            day_start = max(full_day_start, local_now)
            day_end = full_day_end
            if task.deadline_at is not None:
                day_end = min(day_end, task.deadline_at.astimezone(zone))
            if day_end <= day_start:
                continue
            while remaining > 0:
                day_used = _work_minutes(occupied, full_day_start, full_day_end)
                # Existing sessions and proposed sessions count toward the same cap.
                daily_room = preferences.max_daily_minutes - day_used
                if daily_room <= 0:
                    break
                candidate = None
                for open_at, close_at in _free_windows(day_start, day_end, occupied):
                    available = int((close_at - open_at).total_seconds() // 60)
                    length = min(90, remaining, daily_room, available)
                    if length >= min(15, remaining):
                        candidate = (open_at, length)
                        break
                if candidate is None:
                    break
                starts_at, minutes = candidate
                ends_at = starts_at + timedelta(minutes=minutes)
                blocks.append(ProposedBlock(task.task_id, task.title, starts_at, ends_at, minutes))
                occupied.append(BusyInterval(starts_at, ends_at, counts_as_work=True))
                if preferences.min_break_minutes:
                    occupied.append(BusyInterval(ends_at, ends_at + timedelta(minutes=preferences.min_break_minutes)))
                remaining -= minutes
        if remaining:
            unscheduled.append(UnscheduledTask(
                task.task_id, task.title, remaining,
                "Insufficient available time before the deadline or planning horizon",
            ))
    return PlanPreview(tuple(blocks), tuple(unscheduled))
