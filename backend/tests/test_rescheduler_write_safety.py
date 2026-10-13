"""Regression: do not overwrite an occupied rollover target or notify failed moves."""
from unittest.mock import MagicMock

from agents import rescheduler


def state():
    return {
        "uid": "owner", "today": "2026-10-12", "tomorrow": "2026-10-13",
        "incomplete_tasks": [], "tomorrow_tasks": [], "free_slots": [],
        "rescheduled_tasks": [{
            "task_id": "t1", "date": "2026-10-13",
            "start_time": "09:00", "end_time": "10:00",
            "rescheduled_from": "2026-10-12",
        }],
        "errors": [],
    }


def mock_database(monkeypatch, existing):
    current = MagicMock()
    current.exists = True
    current.to_dict.return_value = {
        "date": "2026-10-12", "completed": False, "importance": "important"
    }
    ref = MagicMock()
    ref.get.return_value = current
    db = MagicMock()
    coll = db.collection.return_value.document.return_value.collection.return_value
    coll.document.return_value = ref
    coll.where.return_value.get.return_value = existing
    monkeypatch.setattr(rescheduler, "get_db", lambda: db)
    return ref


def test_live_conflict_skips_task_and_does_not_write(monkeypatch):
    occupied = MagicMock()
    occupied.id = "different-task"
    occupied.to_dict.return_value = {"start_time": "09:30", "end_time": "10:30"}
    ref = mock_database(monkeypatch, [occupied])
    result = rescheduler.write_rescheduled(state())
    assert result["rescheduled_tasks"] == []
    assert any("occupied" in error for error in result["errors"])
    ref.update.assert_not_called()


def test_successful_write_is_reported(monkeypatch):
    ref = mock_database(monkeypatch, [])
    result = rescheduler.write_rescheduled(state())
    assert [task["task_id"] for task in result["rescheduled_tasks"]] == ["t1"]
    ref.update.assert_called_once()


def test_failed_move_does_not_generate_notification(monkeypatch):
    calls = []
    monkeypatch.setattr(rescheduler, "create_notification", lambda *a, **k: calls.append(a))
    sample = state()
    sample["rescheduled_tasks"] = []
    rescheduler.write_notification(sample)
    assert calls == []
