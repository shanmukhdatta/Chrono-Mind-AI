"""Splitting only occurs when the task owner allows it."""
from datetime import datetime, time, timezone
from v2.planner import PlanningTask, PlanningPreferences, preview_schedule


def test_long_unsplittable_task_never_gets_fragmented():
    now = datetime.fromisoformat("2026-10-15T07:00:00+05:30")
    prefs = PlanningPreferences("Asia/Kolkata", time(8), time(20), 480, 10)
    blocked = PlanningTask("u", "Unsplit", 150, splittable=False)
    plan = preview_schedule([blocked], [], prefs, now, 1)
    assert plan.blocks == ()
    assert plan.unscheduled[0].remaining_minutes == 150
    assert "non-splittable" in plan.unscheduled[0].reason


def test_short_unsplittable_task_gets_one_block():
    now = datetime.fromisoformat("2026-10-15T07:00:00+05:30")
    prefs = PlanningPreferences("Asia/Kolkata", time(8), time(20), 480, 10)
    work = PlanningTask("u", "Whole", 75, splittable=False)
    plan = preview_schedule([work], [], prefs, now, 1)
    assert len(plan.blocks) == 1
    assert plan.blocks[0].duration_minutes == 75
