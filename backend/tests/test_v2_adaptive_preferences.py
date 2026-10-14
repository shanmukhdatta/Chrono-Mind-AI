"""Behavior signals influence slot choice only as an optional soft preference."""
from datetime import datetime, time, timezone

from v2.personalization import preferred_work_hour
from v2.planner import BusyInterval, PlanningPreferences, PlanningTask, preview_schedule


def test_threshold_and_duration_weighting():
    assert preferred_work_hour([(18, 1000)] * 4) is None
    assert preferred_work_hour([(8, 100)] * 4 + [(18, 900)]) == 18
    assert preferred_work_hour([(24, 1500)] * 10) is None


def test_preference_changes_slot_without_violating_constraints():
    day = datetime.fromisoformat("2026-10-15T07:00:00+05:30")
    task = PlanningTask("one", "Study", 45)
    without = PlanningPreferences("Asia/Kolkata", time(8), time(20), 480, 10)
    with_behavior = PlanningPreferences("Asia/Kolkata", time(8), time(20), 480, 10, preferred_hour=18)
    first = preview_schedule([task], [], without, day, 1)
    personalized = preview_schedule([task], [], with_behavior, day, 1)
    assert first.blocks[0].starts_at.hour == 8
    assert personalized.blocks[0].starts_at.hour == 18
    busy = [BusyInterval(
        datetime.fromisoformat("2026-10-15T18:00:00+05:30"),
        datetime.fromisoformat("2026-10-15T19:00:00+05:30"),
    )]
    adjusted = preview_schedule([task], busy, with_behavior, day, 1)
    assert adjusted.blocks
    assert all(not (b.starts_at < busy[0].end and b.ends_at > busy[0].start)
               for b in adjusted.blocks)


def test_bidirectional_breaks_between_generated_work():
    day = datetime.fromisoformat("2026-10-15T07:00:00+05:30")
    tasks = [PlanningTask("a", "A", 45), PlanningTask("b", "B", 45)]
    options = PlanningPreferences("Asia/Kolkata", time(8), time(20), 480, 15, 18)
    result = preview_schedule(tasks, [], options, day, 1)
    assert len(result.blocks) == 2
    left, right = sorted(result.blocks, key=lambda b: b.starts_at)
    assert (right.starts_at - left.ends_at).total_seconds() >= 15 * 60
