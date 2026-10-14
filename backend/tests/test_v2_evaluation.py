"""README scheduling-eval release gate; no external API calls or LLM judge."""
from pathlib import Path
from v2.evaluation import evaluate_file

def test_at_least_100_scenario_scheduling_invariants():
    path = Path(__file__).resolve().parents[2] / "evals" / "scenarios.jsonl"
    report = evaluate_file(path)
    assert report["evaluated"] >= 100
    assert report["failed"] == [], report["failed"][:10]
    assert report["validity_rate"] == 1.0
    assert len(report["categories"]) >= 5
