"""Deterministic, DB-free scheduling invariants."""
from datetime import datetime, time, timezone

from v2.planner import (
    BusyInterval, PlanningTask, PlanningPreferences, preview_schedule,
)


def instant(when: str):
    return datetime.fromisoformat(when)


def prefs(maximum=480, break_min=10):
    return PlanningPreferences("Asia/Kolkata", time(8, 0), time(22, 0), maximum, break_min)


def test_avoids_fixed_conflicts_and_limits_work_day():
    tasks = [PlanningTask("a", "Deep Work", 180)]
    fixed = [BusyInterval(instant("2026-10-15T08:00:00+05:30"), instant("2026-10-15T10:00:00+05:30"))]
    result = preview_schedule(tasks, fixed, prefs(maximum=120), instant("2026-10-15T07:00:00+05:30"), 1)
    assert sum(block.duration_minutes for block in result.blocks) == 120
    assert result.unscheduled[0].remaining_minutes == 60
    assert all(block.starts_at >= fixed[0].end for block in result.blocks)
    assert all(result.blocks[i].ends_at <= result.blocks[i+1].starts_at for i in range(len(result.blocks)-1))


def test_deadline_is_strict_and_unfeasible_work_is_kept():
    task = PlanningTask("late", "Submit", 90, deadline_at=instant("2026-10-15T09:00:00+05:30"))
    result = preview_schedule([task], [], prefs(), instant("2026-10-15T08:30:00+05:30"), 3)
    assert len(result.blocks) == 1
    assert result.blocks[0].duration_minutes == 30
    assert result.blocks[0].ends_at <= task.deadline_at
    assert result.unscheduled[0].remaining_minutes == 60


def test_existing_sessions_count_against_daily_cap():
    existing = [BusyInterval(instant("2026-10-15T08:00:00+05:30"), instant("2026-10-15T09:00:00+05:30"), True)]
    result = preview_schedule([PlanningTask("b", "Study", 150)], existing, prefs(maximum=90), instant("2026-10-15T07:00:00+05:30"), 1)
    assert sum(x.duration_minutes for x in result.blocks) == 30
    assert result.unscheduled[0].remaining_minutes == 120


def test_priority_stable_and_inputs_unchanged():
    tasks = [PlanningTask("optional", "Optional", 60, "not_important"), PlanningTask("urgent", "Urgent", 60)]
    before = list(tasks)
    result = preview_schedule(tasks, [], prefs(), instant("2026-10-15T07:00:00+05:30"), 1)
    assert result.blocks[0].task_id == "urgent"
    assert tasks == before


def test_no_past_blocks_and_no_overflow():
    result = preview_schedule([PlanningTask("x", "Task", 60)], [], prefs(), instant("2026-10-15T23:30:00+05:30"), 1)
    assert result.blocks == ()
    assert result.unscheduled[0].remaining_minutes == 60


def test_cross_zone_utc_deadline():
    task = PlanningTask("z", "Timezone", 60, deadline_at=instant("2026-10-15T04:00:00+00:00"))
    result = preview_schedule([task], [], prefs(), instant("2026-10-15T02:00:00+00:00"), 1)
    assert result.blocks
    assert all(b.ends_at.astimezone(timezone.utc) <= task.deadline_at for b in result.blocks)
