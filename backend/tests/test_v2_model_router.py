from v2.model_router import can_answer_without_llm, select_model


def test_no_llm_for_bounded_read_only_task_queries():
    assert can_answer_without_llm("List my pending tasks")
    assert can_answer_without_llm("How many pending tasks do I have?")
    assert not can_answer_without_llm("Create a task named Count")


def test_routing_fast_and_reasoning_models():
    assert select_model("Create a 30 minute task", {}) == "llama-3.1-8b-instant"
    assert select_model("Plan my week with conflicting deadlines", {}) == "llama-3.3-70b-versatile"


def test_unknown_model_rejected():
    import pytest
    with pytest.raises(ValueError):
        select_model("Create a task", {"CHRONOMIND_LLM_FAST_MODEL": "untrusted"})
