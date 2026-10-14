"""Offline deterministic planning evaluation; separate from LLM/provider evaluations."""
import json
from datetime import datetime, time
from pathlib import Path

from v2.planner import BusyInterval, PlanningPreferences, PlanningTask, preview_schedule


def run_case(case: dict) -> dict:
    now = datetime.fromisoformat(case["now"])
    preferences = PlanningPreferences(
        timezone=case["timezone"],
        work_start=time.fromisoformat(case["work_start"]),
        work_end=time.fromisoformat(case["work_end"]),
        max_daily_minutes=case["max_daily_minutes"],
        min_break_minutes=case["min_break_minutes"],
        preferred_hour=case.get("preferred_hour"),
    )
    tasks = [
        PlanningTask(
            task["id"], task["title"], task["minutes"],
            task["importance"],
            datetime.fromisoformat(task["deadline"]) if task.get("deadline") else None,
            task.get("blocked_reason"),
        )
        for task in case["tasks"]
    ]
    busy = [
        BusyInterval(datetime.fromisoformat(item["start"]), datetime.fromisoformat(item["end"]))
        for item in case["busy"]
    ]
    proposal = preview_schedule(tasks, busy, preferences, now, case["days"])
    placed = sum(block.duration_minutes for block in proposal.blocks)
    original = sum(task.remaining_minutes for task in tasks)
    remaining = sum(task.remaining_minutes for task in proposal.unscheduled)
    issues = []
    if placed + remaining != original:
        issues.append("duration_not_conserved")
    all_intervals = sorted(
        [(block.starts_at, block.ends_at) for block in proposal.blocks],
        key=lambda interval: interval[0],
    )
    if any(left[1] > right[0] for left, right in zip(all_intervals, all_intervals[1:])):
        issues.append("proposed_overlap")
    for block in proposal.blocks:
        if block.starts_at < now or block.ends_at <= block.starts_at:
            issues.append("invalid_time")
        for existing in busy:
            if block.starts_at < existing.end and block.ends_at > existing.start:
                issues.append("fixed_event_overlap")
        related = next(task for task in tasks if task.task_id == block.task_id)
        if related.deadline_at and block.ends_at > related.deadline_at:
            issues.append("deadline_violation")
        if related.blocked_reason:
            issues.append("blocked_prerequisite_scheduled")
    outcome = case["expected"]
    if outcome == "complete" and remaining:
        issues.append("feasible_work_unplanned")
    elif outcome == "blocked" and placed:
        issues.append("blocked_work_placed")
    elif outcome == "partial" and (placed == 0 or remaining == 0):
        issues.append("expected_partial_proposal")
    return {
        "id": case["id"], "category": case["category"], "valid": not issues,
        "issues": sorted(set(issues)), "planned_minutes": placed,
        "remaining_minutes": remaining,
    }


def evaluate_file(path: str | Path) -> dict:
    failures = []
    count = 0
    by_category: dict[str, dict[str, int]] = {}
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            result = run_case(json.loads(line))
            count += 1
            group = by_category.setdefault(result["category"], {"passed": 0, "failed": 0})
            group["passed" if result["valid"] else "failed"] += 1
            if not result["valid"]:
                failures.append(result)
    if count < 100:
        raise ValueError("Evaluation dataset must contain at least 100 scenarios")
    return {"evaluated": count, "validity_rate": (count - len(failures))/count,
            "failed": failures, "categories": by_category}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate ChronoMind V2 scheduling invariants")
    parser.add_argument("dataset", nargs="?", default=str(Path(__file__).resolve().parents[2] / "evals" / "scenarios.jsonl"))
    args = parser.parse_args()
    result = evaluate_file(args.dataset)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not result["failed"] else 1)


if __name__ == "__main__":
    main()
