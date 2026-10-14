"""Graph safety: deterministic orchestration, checkpointed human pause and resume."""
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from v2.agent_graph import build_planner_graph, validate_preview


def test_checkpointed_graph_interrupts_before_any_approval():
    calls = []
    preview = {
        "blocks": [{
            "task_id": "t1", "title": "Study", "duration_minutes": 30,
            "starts_at": "2026-10-15T08:00:00+00:00",
            "ends_at": "2026-10-15T08:30:00+00:00",
        }],
        "unscheduled": [], "changes_committed": False,
    }
    def load(owner, days):
        calls.append(("read", owner, days))
        return preview

    def store(owner, run_id, snapshot):
        calls.append(("persist", owner, run_id))
        assert snapshot == preview
        return run_id

    graph = build_planner_graph(load, store, InMemorySaver())
    config = {"configurable": {"thread_id": "alice:run-test"}}
    paused = graph.invoke({"owner_uid": "alice", "run_id": "run-test", "days": 7}, config)
    assert paused["proposal_id"] == "run-test"
    assert paused["status"] == "awaiting_review"
    assert graph.get_state(config).next == ("await_human",)
    assert len(calls) == 2
    resumed = graph.invoke(Command(resume="approved"), config)
    assert resumed["status"] == "approved"
    assert len(calls) == 2  # checkpoint prevents proposal recreation


def test_validation_rejects_overlapping_sessions():
    blocks = [
        {"starts_at": "2026-10-15T08:00:00+00:00", "ends_at": "2026-10-15T09:00:00+00:00", "duration_minutes": 60},
        {"starts_at": "2026-10-15T08:30:00+00:00", "ends_at": "2026-10-15T09:00:00+00:00", "duration_minutes": 30},
    ]
    import pytest
    with pytest.raises(ValueError, match="overlapping"):
        validate_preview({"blocks": blocks})
    with pytest.raises(ValueError, match="No work"):
        validate_preview({"blocks": []})



def test_bounded_replanning_expands_horizon_then_pauses():
    visits = []
    sample = {
        "blocks": [{
            "task_id": "t1", "title": "Study", "duration_minutes": 30,
            "starts_at": "2026-10-16T08:00:00+00:00",
            "ends_at": "2026-10-16T08:30:00+00:00",
        }],
        "unscheduled": [],
    }
    def load(uid, days):
        visits.append(days)
        return sample if days >= 7 else {"blocks": [], "unscheduled": []}
    graph = build_planner_graph(load, lambda uid, run_id, _: run_id, InMemorySaver())
    config = {"configurable": {"thread_id": "alice:replan-test"}}
    result = graph.invoke({"owner_uid": "alice", "run_id": "retry-run", "days": 3}, config)
    assert visits == [3, 5, 7]
    assert result["attempt"] == 2
    assert result["status"] == "awaiting_review"
    assert graph.get_state(config).next == ("await_human",)


def test_no_solution_stops_after_three_attempts_without_proposal():
    visits = []
    def load(uid, days):
        visits.append(days)
        return {"blocks": [], "unscheduled": []}
    def forbidden(*args):
        raise AssertionError("Invalid proposals must not be persisted")
    graph = build_planner_graph(load, forbidden, InMemorySaver())
    config = {"configurable": {"thread_id": "alice:exhausted"}}
    result = graph.invoke({"owner_uid": "alice", "run_id": "no-solution", "days": 3}, config)
    assert visits == [3, 5, 7]
    assert result["status"] == "no_feasible_plan"
    assert "No work fits" in result["validation_error"]
    assert graph.get_state(config).next == ()
