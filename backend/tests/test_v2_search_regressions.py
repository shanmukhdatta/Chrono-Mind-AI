"""Pure algorithm regressions; runnable using unittest without service credentials."""
import random
import unittest
from dataclasses import replace
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from v2.planner import (
    BusyInterval, PlanningTask, PlanningPreferences, PlanPreview, ProposedBlock,
    preview_schedule,
)
from v2.priority import context_matches
from v2.replanning import choose_schedule, _valid, _quality, MAX_CANDIDATES


class SearchRegressions(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 24, 8, tzinfo=timezone.utc)
        self.options = PlanningPreferences("UTC", time(8), time(18), 120, 0)

    def test_deadline_order_rescues_urgent_task(self):
        tasks = [
            PlanningTask("later", "Later", 60, priority_score=90,
                         deadline_at=self.now + timedelta(hours=3)),
            PlanningTask("urgent", "Urgent", 60, priority_score=50,
                         deadline_at=self.now + timedelta(hours=1)),
        ]
        baseline = preview_schedule(tasks, [], self.options, self.now, 1)
        plan, trace = choose_schedule(tasks, [], self.options, self.now, 1)
        self.assertTrue(baseline.unscheduled)
        self.assertFalse(plan.unscheduled)
        self.assertEqual(plan.blocks[0].task_id, "urgent")
        self.assertGreater(_quality(plan, tasks), _quality(baseline, tasks))
        self.assertFalse(trace["learned_policy"])

    def test_short_tasks_are_not_dominated_by_long_task_minutes(self):
        tasks = [PlanningTask("long", "Long", 120, priority_score=80),
                 PlanningTask("short1", "Short", 30, priority_score=70),
                 PlanningTask("short2", "Short", 30, priority_score=70)]
        plan, _ = choose_schedule(tasks, [], replace(self.options, max_daily_minutes=60), self.now, 1)
        self.assertEqual({b.task_id for b in plan.blocks}, {"short1", "short2"})

    def test_overlapping_imports_count_once(self):
        busy = [BusyInterval(self.now, self.now + timedelta(hours=1), True)] * 2
        plan, _ = choose_schedule([PlanningTask("x", "X", 60)], busy, self.options, self.now, 1)
        self.assertEqual(sum(b.duration_minutes for b in plan.blocks), 60)

    def test_rejects_duplicate_ids_and_naive_deadlines(self):
        with self.assertRaises(ValueError):
            choose_schedule([PlanningTask("x", "X", 15)] * 2, [], self.options, self.now, 1)
        with self.assertRaises(ValueError):
            choose_schedule([PlanningTask("x", "X", 15, deadline_at=datetime(2026, 11, 25))],
                            [], self.options, self.now, 1)

    def test_context_does_not_match_inside_words(self):
        self.assertFalse(context_matches("art", ["cartography"]))
        self.assertFalse(context_matches("exam", ["example"]))
        self.assertTrue(context_matches("Placement Season", ["placement prep"]))

    def test_validator_checks_real_duration_and_conservation(self):
        task = PlanningTask("x", "X", 30)
        block = ProposedBlock("x", "X", self.now, self.now + timedelta(minutes=20), 30)
        valid, errors = _valid(PlanPreview((block,), ()), [], [task], self.options, self.now, 1)
        self.assertFalse(valid)
        self.assertIn("INVALID_BLOCK", errors)
        valid, errors = _valid(PlanPreview((), ()), [], [task], self.options, self.now, 1)
        self.assertIn("DURATION_NOT_CONSERVED", errors)

    def test_validator_checks_break_cap_and_window(self):
        task = PlanningTask("x", "X", 30)
        first = ProposedBlock("x", "X", self.now, self.now + timedelta(minutes=15), 15)
        second = ProposedBlock("x", "X", first.ends_at, first.ends_at + timedelta(minutes=15), 15)
        options = replace(self.options, min_break_minutes=10, max_daily_minutes=20)
        _, errors = _valid(PlanPreview((first, second), ()), [], [task], options, self.now, 1)
        self.assertIn("BREAK_VIOLATION", errors)
        self.assertIn("DAILY_CAP_VIOLATION", errors)
        outside = replace(first, starts_at=self.now - timedelta(hours=1),
                          ends_at=self.now - timedelta(minutes=45))
        _, errors = _valid(PlanPreview((outside,), ()), [], [task], options, self.now, 1)
        self.assertIn("WORK_WINDOW_VIOLATION", errors)
        self.assertIn("PAST_BLOCK", errors)

    def test_daylight_saving_duration_uses_elapsed_time(self):
        zone = ZoneInfo("America/New_York")
        for now in [datetime(2026, 3, 8, 0, tzinfo=zone), datetime(2026, 11, 1, 0, tzinfo=zone)]:
            options = PlanningPreferences("America/New_York", time(0), time(5), 300, 0)
            plan, _ = choose_schedule([PlanningTask("x", "X", 240)], [], options, now, 1)
            for block in plan.blocks:
                elapsed = block.ends_at.astimezone(timezone.utc) - block.starts_at.astimezone(timezone.utc)
                self.assertEqual(elapsed.total_seconds(), block.duration_minutes * 60)
            self.assertFalse(plan.unscheduled)

    def test_output_preserves_preferred_local_hour(self):
        options = PlanningPreferences("Asia/Kolkata", time(8), time(20), 120, 10, 18)
        plan, _ = choose_schedule([PlanningTask("x", "X", 45)], [], options, self.now, 1)
        self.assertEqual(plan.blocks[0].starts_at.hour, 18)
        self.assertEqual(str(plan.blocks[0].starts_at.tzinfo), "Asia/Kolkata")

    def test_randomized_feasibility_and_baseline_quality(self):
        rng = random.Random(42)
        for _ in range(60):
            tasks = [PlanningTask(str(i), str(i), rng.choice([15, 30, 60, 90, 120]),
                                  priority_score=rng.randint(1, 100),
                                  deadline_at=self.now + timedelta(hours=rng.randint(1, 10)),
                                  splittable=rng.choice([True, False]))
                     for i in range(rng.randint(1, 8))]
            options = replace(self.options, min_break_minutes=rng.choice([0, 10, 15]))
            busy = [BusyInterval(self.now + timedelta(hours=2), self.now + timedelta(hours=3))]
            before = list(tasks)
            baseline = preview_schedule(tasks, busy, options, self.now, 1)
            plan, trace = choose_schedule(tasks, busy, options, self.now, 1)
            self.assertTrue(_valid(plan, busy, tasks, options, self.now, 1)[0])
            self.assertGreaterEqual(_quality(plan, tasks), _quality(baseline, tasks))
            self.assertLessEqual(trace["candidates_checked"], MAX_CANDIDATES)
            self.assertEqual(tasks, before)
            self.assertEqual((plan, trace), choose_schedule(tasks, busy, options, self.now, 1))


if __name__ == "__main__":
    unittest.main()
