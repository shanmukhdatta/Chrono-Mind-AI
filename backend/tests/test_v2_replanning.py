"""Bounded alternate planning and durable explanation API contracts."""
from datetime import datetime, time

from v2.replanning import choose_schedule, MAX_CANDIDATES
from v2.planner import BusyInterval, PlanningPreferences, PlanningTask


def test_bounded_replanning_never_exceeds_three_candidates():
    now = datetime.fromisoformat("2026-10-15T07:00:00+05:30")
    options = PlanningPreferences("Asia/Kolkata", time(8), time(14), 60, 10)
    tasks = [PlanningTask("a", "A", 90, priority_score=80),
             PlanningTask("b", "B", 90, priority_score=50)]
    plan, trace = choose_schedule(tasks, [], options, now, days=1)
    assert 1 <= trace["candidates_checked"] <= MAX_CANDIDATES == 3
    assert trace["chosen"] in {"priority", "deadline_first", "short_jobs_first"}
    assert sum(b.duration_minutes for b in plan.blocks) <= 60
    assert sum(t.remaining_minutes for t in plan.unscheduled) >= 120
    assert all(a["valid"] for a in trace["attempts"])


def test_empty_tasks_return_explainable_empty_proposal():
    now = datetime.fromisoformat("2026-10-15T07:00:00+05:30")
    options = PlanningPreferences("Asia/Kolkata", time(8), time(18), 480, 10)
    plan, trace = choose_schedule([], [], options, now, 3)
    assert trace["candidates_checked"] == 0
    assert not plan.blocks
