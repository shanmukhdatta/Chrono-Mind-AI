"""Bounded routing and real non-content latency metrics."""
from v2.llm_router import choose_route, simple_answer


def test_fast_no_llm_and_reasoning_routes():
    assert choose_route("How many tasks are pending?").tier == "no_llm"
    assert choose_route("Plan my week around exams").tier == "reasoning"
    assert choose_route("Create a 25 minute study task").tier == "fast"
    assert "2 pending tasks" in simple_answer({"tasks":[{},{}],"goals":[{}]})


def test_model_identifiers_are_strict_and_no_guessing():
    assert choose_route("Count my tasks").model is None
    decision = choose_route("Break down a complex goal into steps")
    assert decision.model and decision.reason
