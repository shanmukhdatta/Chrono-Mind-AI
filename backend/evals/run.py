"""Reproducible, offline scheduling-quality evaluation suite.

Reads versioned fixtures (never live user data), measures constraints, reports
actual latency and unscheduled work. This is NOT an LLM benchmark.
"""
import argparse
import json
import statistics
import time
from datetime import datetime, time as clock_time, timedelta
from pathlib import Path

from v2.planner import BusyInterval, PlanningPreferences, PlanningTask, preview_schedule

DEFAULT_CASES = Path(__file__).with_name("scenarios.jsonl")


def check_case(case: dict):
    now = datetime.fromisoformat(case["now"])
    settings = PlanningPreferences(
        case["timezone"], clock_time.fromisoformat(case["work_start"]),
        clock_time.fromisoformat(case["work_end"]),
        case["max_daily_minutes"], case["break_minutes"],
        case["preferred_hour"],
    )
    tasks = [PlanningTask(
        item["id"], item["title"], item["minutes"], item["importance"],
        datetime.fromisoformat(item["deadline"]) if item.get("deadline") else None,
        "Prerequisite incomplete" if item.get("blocked") else None, item["priority"],
    ) for item in case["tasks"]]
    fixed = [BusyInterval(datetime.fromisoformat(item["start"]), datetime.fromisoformat(item["end"])) for item in case["busy"]]
    t0 = time.perf_counter()
    plan = preview_schedule(tasks, fixed, settings, now, case["horizon_days"])
    elapsed_ms = (time.perf_counter() - t0) * 1000
    errors = []
    blocks = sorted(plan.blocks, key=lambda b:b.starts_at)
    originals = {task.task_id:task for task in tasks}
    for i, block in enumerate(blocks):
        if block.starts_at < now: errors.append("past")
        if block.ends_at <= block.starts_at: errors.append("non_positive")
        if block.duration_minutes != (block.ends_at-block.starts_at).total_seconds()//60:
            errors.append("duration_mismatch")
        if block.starts_at.hour < settings.work_start.hour or block.ends_at.hour > settings.work_end.hour:
            errors.append("work_window")
        if originals[block.task_id].deadline_at and block.ends_at > originals[block.task_id].deadline_at:
            errors.append("deadline")
        if originals[block.task_id].blocked_reason:
            errors.append("blocked_dependency")
        for event in fixed:
            if block.starts_at < event.end and block.ends_at > event.start:
                errors.append("fixed_overlap")
        for prev in blocks[:i]:
            if block.starts_at < prev.ends_at and block.ends_at > prev.starts_at:
                errors.append("task_overlap")
    for task in tasks:
        assigned = sum(b.duration_minutes for b in blocks if b.task_id == task.task_id)
        outstanding = sum(u.remaining_minutes for u in plan.unscheduled if u.task_id == task.task_id)
        if assigned + outstanding != task.remaining_minutes:
            errors.append("missing_or_duplicate_effort")
    for day_offset in range(case["horizon_days"]):
        day = now.date()+timedelta(days=day_offset)
        used = sum(b.duration_minutes for b in blocks if b.starts_at.date() == day)
        if used > settings.max_daily_minutes: errors.append("daily_limit")
    return {"name":case["name"],"valid":not errors,"errors":sorted(set(errors)),
        "latency_ms":round(elapsed_ms,4),"planned_minutes":sum(b.duration_minutes for b in blocks),
        "unscheduled_minutes":sum(u.remaining_minutes for u in plan.unscheduled)}


def run_suite(path: Path = DEFAULT_CASES) -> dict:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    outcomes = [check_case(case) for case in records]
    if not outcomes:
        raise ValueError("Evaluation fixture file is empty")
    ms = [row["latency_ms"] for row in outcomes]
    return {
        "scenario_count":len(outcomes),
        "valid_schedules":sum(row["valid"] for row in outcomes),
        "schedule_validity_rate":round(sum(row["valid"] for row in outcomes)/len(outcomes),4),
        "total_unscheduled_minutes":sum(row["unscheduled_minutes"] for row in outcomes),
        "mean_latency_ms":round(statistics.mean(ms),3),
        "p95_latency_ms":round(sorted(ms)[max(0,int(0.95*len(ms))-1)],3),
        "failed_scenarios":[{"name":row["name"],"errors":row["errors"]} for row in outcomes if not row["valid"]],
        "scope":"offline deterministic scheduler only; no LLM/API/PostgreSQL end-to-end claims",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--cases",type=Path,default=DEFAULT_CASES)
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    report=run_suite(args.cases)
    summary=json.dumps(report,indent=2)
    print(summary)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(summary+"\n",encoding="utf-8")
    return 0 if not report["failed_scenarios"] else 1


if __name__=="__main__":
    raise SystemExit(main())
