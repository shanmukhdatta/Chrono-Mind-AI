"""Compatibility gate for the modern LangGraph checkpointing packages."""
from typing import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver


class State(TypedDict):
    count: int


def test_graph_api_and_thread_checkpoint():
    builder = StateGraph(State)
    builder.add_node("increase", lambda state: {"count": state["count"] + 1})
    builder.set_entry_point("increase")
    builder.add_edge("increase", END)
    graph = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "isolated-regression-thread"}}
    assert graph.invoke({"count": 1}, config)["count"] == 2
    assert graph.get_state(config).values["count"] == 2


def test_postgres_saver_is_importable_without_side_effects():
    assert callable(PostgresSaver.from_conn_string)
