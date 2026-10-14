"""Deterministic scenarios catch scheduling regressions before release."""
from evals.run import DEFAULT_CASES, run_suite


def test_120_versioned_scheduling_scenarios():
    result = run_suite(DEFAULT_CASES)
    assert result["scenario_count"] >= 100
    assert result["failed_scenarios"] == []
    assert result["schedule_validity_rate"] == 1.0
