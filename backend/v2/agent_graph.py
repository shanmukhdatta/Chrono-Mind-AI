"""Stateful LangGraph planner with durable pause for human review.

The graph is parameterized by real read/persist functions. It contains no
autonomous approval or calendar-write node.
"""
from typing import Callable, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.types import interrupt


class AgentState(TypedDict, total=False):
    owner_uid: str
    run_id: str
    days: int
    preview: dict
    proposal_id: str
    decision: str
    status: str
    attempt: int
    validation_error: str


def validate_preview(preview: dict) -> None:
    blocks = preview.get("blocks", [])
    if not blocks:
        raise ValueError("No work fits within the requested planning horizon")
    if len(blocks) > 500:
        raise ValueError("Proposal is too large")
    intervals = []
    for block in blocks:
        from datetime import datetime
        start = datetime.fromisoformat(block["starts_at"])
        end = datetime.fromisoformat(block["ends_at"])
        if start.tzinfo is None or end.tzinfo is None or end <= start:
            raise ValueError("Invalid proposed session")
        if not 1 <= int(block["duration_minutes"]) <= 90:
            raise ValueError("Invalid proposed task duration")
        intervals.append((start, end))
    intervals.sort(key=lambda item: item[0])
    for current, later in zip(intervals, intervals[1:]):
        if current[1] > later[0]:
            raise ValueError("The suggested schedule contains overlapping blocks")


def build_planner_graph(
    load_preview: Callable[[str, int], dict],
    persist_proposal: Callable[[str, str, dict], str],
    checkpointer,
):
    def intake(state: AgentState) -> AgentState:
        if not state.get("owner_uid") or not state.get("run_id"):
            raise ValueError("A verified owner and unique run id are required")
        if not 1 <= int(state.get("days", 0)) <= 14:
            raise ValueError("Planning horizon must be 1..14 days")
        return {"status": "planning", "attempt": 0, "validation_error": ""}

    def generate(state: AgentState) -> AgentState:
        # At most three deterministic attempts, broadening the horizon by two days.
        horizon = min(14, state["days"] + state.get("attempt", 0) * 2)
        preview = load_preview(state["owner_uid"], horizon)
        return {"preview": preview, "status": "validating"}

    def validate(state: AgentState) -> AgentState:
        try:
            validate_preview(state["preview"])
            return {"validation_error": "", "status": "awaiting_persistence"}
        except ValueError as exc:
            return {"validation_error": str(exc), "status": "replanning"}

    def route_validation(state: AgentState) -> str:
        if not state.get("validation_error"):
            return "valid"
        if state.get("attempt", 0) < 2:
            return "retry"
        return "exhausted"

    def retry(state: AgentState) -> AgentState:
        return {"attempt": state.get("attempt", 0) + 1}

    def no_plan(state: AgentState) -> AgentState:
        return {"status": "no_feasible_plan"}

    def store(state: AgentState) -> AgentState:
        proposal_id = persist_proposal(state["owner_uid"], state["run_id"], state["preview"])
        return {"proposal_id": proposal_id, "status": "awaiting_review"}

    def await_human(state: AgentState) -> AgentState:
        decision = interrupt({
            "proposal_id": state["proposal_id"],
            "message": "Review and approve or reject the persisted proposal in ChronoMind.",
        })
        if decision not in ("approved", "rejected", "undone"):
            raise ValueError("Unsupported approval decision")
        return {"decision": decision}

    def complete(state: AgentState) -> AgentState:
        # The actual calendar transaction is handled by the separately authenticated
        # proposal approval API before this state can be resumed.
        return {"status": state["decision"]}

    graph = StateGraph(AgentState)
    graph.add_node("intake", intake)
    graph.add_node("generate", generate)
    graph.add_node("validate", validate)
    graph.add_node("retry", retry)
    graph.add_node("no_plan", no_plan)
    graph.add_node("store", store)
    graph.add_node("await_human", await_human)
    graph.add_node("complete", complete)
    graph.set_entry_point("intake")
    graph.add_edge("intake", "generate")
    graph.add_edge("generate", "validate")
    graph.add_conditional_edges("validate", route_validation, {
        "valid": "store", "retry": "retry", "exhausted": "no_plan",
    })
    graph.add_edge("retry", "generate")
    graph.add_edge("no_plan", END)
    graph.add_edge("store", "await_human")
    graph.add_edge("await_human", "complete")
    graph.add_edge("complete", END)
    return graph.compile(checkpointer=checkpointer)
