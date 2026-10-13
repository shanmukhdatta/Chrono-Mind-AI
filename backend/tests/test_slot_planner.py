"""No network or Firebase required: deterministic rollover safety regressions."""
from datetime import date, timedelta

import pytest

from agents.slot_planner import free_intervals, plan_rollover


def task(task_id, day="2026-10-12", duration=60):
    return {
        "task_id": task_id, "title": task_id, "date": day,
        "duration_minutes": duration,
        "start_time": "09:00", "end_time": "10:00",
        "importance": "important", "completed": False,
    }


def test_two_long_tasks_never_share_future_slot():
    initial = [task("a", duration=600), task("b", duration=600)]
    existing = {"2026-10-13": [{"start_time": "08:00", "end_time": "20:00"}]}
    placements, missing = plan_rollover(initial, "2026-10-13", lambda d: existing.get(d, []))
    assert not missing
    assert len(placements) == 2
    assert placements[0]["date"] != placements[1]["date"]
    assert placements[0]["date"] == "2026-10-14"
    assert placements[1]["date"] == "2026-10-15"


def test_each_placement_reserves_part_of_same_day():
    tasks = [task("a", duration=60), task("b", duration=90), task("c", duration=30)]
    placements, missing = plan_rollover(tasks, "2026-10-13", lambda d: [])
    assert not missing
    assert [(t["start_time"], t["end_time"]) for t in placements] == [
        ("08:00", "09:00"), ("09:00", "10:30"), ("10:30", "11:00")
    ]


def test_lookahead_includes_next_day_and_seventh_day():
    first = date(2026, 10, 13)
    busy = {
        (first + timedelta(days=i)).isoformat():
        [{"start_time": "08:00", "end_time": "22:00"}]
        for i in range(6)
    }
    dates_requested = []
    def loader(day):
        dates_requested.append(day)
        return busy.get(day, [])
    placements, missing = plan_rollover([task("a")], first.isoformat(), loader)
    assert not missing
    assert placements[0]["date"] == "2026-10-19"
    assert dates_requested == [(first + timedelta(days=i)).isoformat() for i in range(7)]


def test_unschedulable_is_preserved_not_modified():
    one = task("overflow", duration=850)
    placements, missing = plan_rollover([one], "2026-10-13", lambda d: [])
    assert placements == [] and missing == ["overflow"]
    assert one["date"] == "2026-10-12"


def test_existing_overlaps_are_merged_and_not_double_booked():
    existing = [
        {"start_time": "08:00", "end_time": "10:00"},
        {"start_time": "09:00", "end_time": "13:00"},
    ]
    assert free_intervals(existing) == [(780, 1320)]


def test_invalid_existing_appointment_fails_closed():
    with pytest.raises(ValueError):
        plan_rollover([task("a")], "2026-10-13",
                      lambda d: [{"start_time": "15:00", "end_time": "14:00"}])


def test_original_data_remains_unchanged():
    one = task("a")
    existing = [{"start_time": "10:00", "end_time": "11:00"}]
    plan_rollover([one], "2026-10-13", lambda d: existing)
    assert one["date"] == "2026-10-12"
    assert len(existing) == 1
