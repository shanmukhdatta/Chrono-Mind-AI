"""Bounded, deterministic alternative scheduling and explainable quality scoring.

This is a greedy candidate search, not full mathematical optimization.
"""
from dataclasses import replace
from datetime import datetime, timezone
from dataclasses import dataclass

from .planner import (
    BusyInterval, PlanPreview, PlanningPreferences,
    PlanningTask, preview_schedule,
)

MAX_CANDIDATES = 3


def _quality(plan: PlanPreview, tasks: list[PlanningTask]) -> int:
    weights = {t.task_id: max(1, t.priority_score) for t in tasks}
    return sum(b.duration_minutes * weights[b.task_id] for b in plan.blocks)


def _valid(plan: PlanPreview, busy: list[BusyInterval], tasks: list[PlanningTask]) -> tuple[bool, list[str]]:
    errors = []
    task_map = {t.task_id: t for t in tasks}
    candidate = sorted(plan.blocks, key=lambda b: b.starts_at)
    for i, block in enumerate(candidate):
        task = task_map.get(block.task_id)
        if task is None:
            errors.append("UNKNOWN_TASK")
            continue
        if block.ends_at <= block.starts_at or not 1 <= block.duration_minutes <= 90:
            errors.append("INVALID_BLOCK")
        if task.deadline_at is not None and block.ends_at > task.deadline_at:
            errors.append("DEADLINE_VIOLATION")
        if task.blocked_reason:
            errors.append("DEPENDENCY_VIOLATION")
        if i and candidate[i - 1].ends_at > block.starts_at:
            errors.append("TASK_OVERLAP")
        if any(block.starts_at < fixed.end and block.ends_at > fixed.start for fixed in busy):
            errors.append("FIXED_EVENT_OVERLAP")
    return not errors, sorted(set(errors))


def choose_schedule(
    tasks: list[PlanningTask],
    busy: list[BusyInterval],
    options: PlanningPreferences,
    now: datetime,
    days: int,
) -> tuple[PlanPreview, dict]:
    """Try at most 3 explainable ranking strategies and return the best valid plan."""
    if not tasks:
        return PlanPreview((), ()), {"candidates_checked": 0, "chosen": "none", "attempts": []}
    rankings = [
        ("priority", tasks),
        ("deadline_first", [
            replace(t, priority_score=t.priority_score + (500 if t.deadline_at else 0))
            for t in tasks
        ]),
        ("short_jobs_first", [
            replace(t, priority_score=t.priority_score + max(0, 120-t.remaining_minutes))
            for t in tasks
        ]),
    ]
    attempts = []
    winner = None
    winning_score = None
    selected = None
    for name, ranking in rankings[:MAX_CANDIDATES]:
        plan = preview_schedule(ranking, busy, options, now, days)
        valid, errors = _valid(plan, busy, tasks)
        score = _quality(plan, tasks) if valid else -1
        attempts.append({
            "strategy": name, "valid": valid, "reason_codes": errors,
            "planned_minutes": sum(b.duration_minutes for b in plan.blocks),
            "unscheduled_minutes": sum(t.remaining_minutes for t in plan.unscheduled),
            "quality_score": score,
        })
        if valid and (winner is None or score > winning_score):
            winner, winning_score, selected = plan, score, name
        if name == "priority" and valid and not plan.unscheduled:
            break
    if winner is None:
        raise ValueError("No valid plan could be produced with bounded candidate search")
    return winner, {
        "candidates_checked": len(attempts),
        "chosen": selected,
        "attempts": attempts,
        "quality_score": winning_score,
        "max_candidate_attempts": MAX_CANDIDATES,
    }
