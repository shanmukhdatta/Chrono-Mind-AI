"""Regression tests: preserve unfinished optional work during rollover."""

from agents.missed_task_policy import select_rollover_candidates


def test_only_unfinished_important_tasks_are_rollover_candidates():
    tasks = [
        {"task_id": "important", "importance": "important", "completed": False},
        {"task_id": "optional", "importance": "not_important", "completed": False},
        {"task_id": "done", "importance": "important", "completed": True},
    ]
    selected = select_rollover_candidates(tasks)
    assert [t["task_id"] for t in selected] == ["important"]
    assert len(tasks) == 3


def test_empty_input_and_missing_importance_are_safe():
    assert select_rollover_candidates([]) == []
    assert select_rollover_candidates([{"task_id": "legacy", "completed": False}]) == []


def test_selected_tasks_are_copied_not_mutated():
    original = {"task_id": "one", "importance": "important", "completed": False}
    selected = select_rollover_candidates([original])
    selected[0]["date"] = "2026-10-13"
    assert "date" not in original
