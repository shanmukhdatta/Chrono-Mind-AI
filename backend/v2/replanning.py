"""Bounded task-order search; not a learned policy or a global optimum."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from zoneinfo import ZoneInfo

from .planner import (
    BusyInterval, PlanPreview, PlanningPreferences, PlanningTask,
    preview_schedule, _work_minutes,
)

MAX_CANDIDATES = 32
SEARCH_TASK_LIMIT = 12
BEAM_WIDTH = 4


def _quality(plan: PlanPreview, tasks: list[PlanningTask]) -> Fraction:
    """Importance-weighted task progress instead of rewarding long tasks."""
    placed = defaultdict(int)
    for block in plan.blocks:
        placed[block.task_id] += block.duration_minutes
    return sum(
        (
            Fraction(max(1, task.priority_score) * placed[task.task_id], task.remaining_minutes)
            for task in tasks if task.remaining_minutes > 0
        ),
        Fraction(),
    )


def _valid(
    plan: PlanPreview,
    busy: list[BusyInterval],
    tasks: list[PlanningTask],
    options: PlanningPreferences | None = None,
    now: datetime | None = None,
    days: int | None = None,
) -> tuple[bool, list[str]]:
    errors = []
    task_map = {task.task_id: task for task in tasks}
    candidate = sorted(plan.blocks, key=lambda block: block.starts_at.astimezone(timezone.utc))
    totals = defaultdict(int)
    counts = defaultdict(int)
    remaining = {}
    for item in plan.unscheduled:
        if item.task_id not in task_map or item.task_id in remaining or item.remaining_minutes <= 0:
            errors.append("INVALID_UNSCHEDULED")
        remaining[item.task_id] = item.remaining_minutes
    zone = ZoneInfo(options.timezone) if options else None
    work = [
        BusyInterval(item.start.astimezone(timezone.utc), item.end.astimezone(timezone.utc), item.counts_as_work)
        for item in busy
    ]
    for i, block in enumerate(candidate):
        task = task_map.get(block.task_id)
        if task is None:
            errors.append("UNKNOWN_TASK")
            continue
        start, end = block.starts_at, block.ends_at
        if any(value.tzinfo is None or value.utcoffset() is None for value in (start, end)):
            errors.append("NAIVE_TIME")
            continue
        start, end = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
        totals[task.task_id] += block.duration_minutes
        counts[task.task_id] += 1
        if end <= start or not 1 <= block.duration_minutes <= 90 or (end - start).total_seconds() != block.duration_minutes * 60:
            errors.append("INVALID_BLOCK")
        if task.earliest_start_at is not None and start < task.earliest_start_at.astimezone(timezone.utc):
            errors.append("RELEASE_DATE_VIOLATION")
        if task.deadline_at is not None and end > task.deadline_at:
            errors.append("DEADLINE_VIOLATION")
        if task.blocked_reason:
            errors.append("DEPENDENCY_VIOLATION")
        if now is not None and start < now:
            errors.append("PAST_BLOCK")
        if i and candidate[i - 1].ends_at.astimezone(timezone.utc) > start:
            errors.append("TASK_OVERLAP")
        for fixed in busy:
            if start < fixed.end and end > fixed.start:
                errors.append("FIXED_EVENT_OVERLAP")
        if options:
            padding = timedelta(minutes=options.min_break_minutes)
            for fixed in work:
                if fixed.counts_as_work and start < fixed.end + padding and end > fixed.start - padding:
                    errors.append("BREAK_VIOLATION")
            local_day = start.astimezone(zone).date()
            low = datetime.combine(local_day, options.work_start, zone).astimezone(timezone.utc)
            high = datetime.combine(local_day, options.work_end, zone).astimezone(timezone.utc)
            if start < low or end > high:
                errors.append("WORK_WINDOW_VIOLATION")
            if now is not None and days is not None:
                offset = (local_day - now.astimezone(zone).date()).days
                if not 0 <= offset < days:
                    errors.append("HORIZON_VIOLATION")
            work.append(BusyInterval(start, end, True))
            if _work_minutes(work, low, high) > options.max_daily_minutes:
                errors.append("DAILY_CAP_VIOLATION")
    for task in tasks:
        if totals[task.task_id] + remaining.get(task.task_id, 0) != task.remaining_minutes:
            errors.append("DURATION_NOT_CONSERVED")
        if not task.splittable and totals[task.task_id] and (
            counts[task.task_id] != 1 or totals[task.task_id] != task.remaining_minutes
        ):
            errors.append("SPLIT_VIOLATION")
    return not errors, sorted(set(errors))


def choose_schedule(
    tasks: list[PlanningTask],
    busy: list[BusyInterval],
    options: PlanningPreferences,
    now: datetime,
    days: int,
) -> tuple[PlanPreview, dict]:
    """Search insertion neighborhoods with deterministic ties and a fixed budget.

    Placement within an order stays greedy. Existing blocks remain immutable.
    """
    baseline = preview_schedule(tasks, busy, options, now, days)
    if not tasks:
        return baseline, {"candidates_checked": 0, "chosen": "none", "attempts": []}
    latest = datetime.max.replace(tzinfo=timezone.utc)
    priority = sorted(
        tasks,
        key=lambda task: (-task.priority_score, task.importance != "important", task.deadline_at or latest, task.task_id),
    )
    seeds = [
        ("priority", priority),
        ("deadline_first", sorted(tasks, key=lambda task: (task.deadline_at or latest, -task.priority_score, task.task_id))),
        ("short_jobs_first", sorted(tasks, key=lambda task: (task.remaining_minutes, -task.priority_score, task.task_id))),
    ]
    attempts, evaluated, seen = [], [], set()

    def evaluate(name, order):
        key = tuple(task.task_id for task in order)
        if key in seen or len(attempts) >= MAX_CANDIDATES:
            return
        seen.add(key)
        plan = preview_schedule(order, busy, options, now, days, preserve_order=True)
        valid, errors = _valid(plan, busy, tasks, options, now, days)
        quality = _quality(plan, tasks) if valid else Fraction(-1)
        planned = sum(block.duration_minutes for block in plan.blocks)
        attempts.append({
            "strategy": name,
            "valid": valid,
            "reason_codes": errors,
            "planned_minutes": planned,
            "unscheduled_minutes": sum(item.remaining_minutes for item in plan.unscheduled),
            "quality_score": float(quality),
        })
        if valid:
            evaluated.append((quality, planned, -len(plan.blocks), name, order, plan))

    for name, order in seeds:
        evaluate(name, order)
    expanded = set()
    while len(attempts) < MAX_CANDIDATES:
        frontier = sorted(evaluated, key=lambda item: item[:3], reverse=True)[:BEAM_WIDTH]
        before = len(attempts)
        for _, _, _, _, order, _ in frontier:
            key = tuple(task.task_id for task in order)
            if key in expanded:
                continue
            expanded.add(key)
            for source in range(1, min(len(order), SEARCH_TASK_LIMIT)):
                for destination in range(source):
                    neighbor = list(order)
                    neighbor.insert(destination, neighbor.pop(source))
                    evaluate("order_search", neighbor)
                    if len(attempts) >= MAX_CANDIDATES:
                        break
                if len(attempts) >= MAX_CANDIDATES:
                    break
        if len(attempts) == before:
            break
    if not evaluated:
        raise ValueError("No valid plan could be produced with bounded candidate search")
    winner = max(evaluated, key=lambda item: item[:3])
    return winner[5], {
        "candidates_checked": len(attempts),
        "chosen": winner[3],
        "attempts": attempts,
        "quality_score": float(winner[0]),
        "max_candidate_attempts": MAX_CANDIDATES,
        "method": "bounded task-order search",
        "objective": "importance-weighted fraction of each task scheduled",
        "optimality_guaranteed": False,
        "learned_policy": False,
        "search_task_limit": SEARCH_TASK_LIMIT,
    }
