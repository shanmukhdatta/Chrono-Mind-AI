"""Contract regressions for Firestore-backed task updates (database mocked)."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from models.task import TaskUpdate
from services import task_service


@pytest.fixture
def stored_task(monkeypatch):
    snapshot = MagicMock()
    snapshot.exists = True
    snapshot.id = "t1"
    snapshot.to_dict.return_value = {
        "uid": "owner", "title": "Study", "date": "2026-10-13",
        "start_time": "09:00", "end_time": "10:00",
        "created_at": datetime(2026, 10, 12, 3, 0, tzinfo=timezone.utc),
    }
    reference = MagicMock()
    reference.get.return_value = snapshot
    db = MagicMock()
    db.collection.return_value.document.return_value.collection.return_value.document.return_value = reference
    monkeypatch.setattr(task_service, "get_db", lambda: db)
    return reference, snapshot


def test_date_only_update_checks_conflicts(stored_task, monkeypatch):
    reference, snapshot = stored_task
    queried = []
    def record(*args, **kwargs):
        queried.append((args, kwargs))
        return None
    monkeypatch.setattr(task_service, "check_time_conflict", record)
    response = task_service.update_task("owner", "t1", TaskUpdate(date="2026-10-14"))
    assert queried == [
        (("owner", "2026-10-14", "09:00", "10:00"), {"exclude_task_id": "t1"})
    ]
    assert reference.update.call_args.args[0]["duration_minutes"] == 60
    json.dumps(response)


def test_date_only_update_blocks_occupied_slot(stored_task, monkeypatch):
    reference, _ = stored_task
    monkeypatch.setattr(task_service, "check_time_conflict", lambda *a, **k: {
        "title": "Busy", "start_time": "09:00", "end_time": "10:00",
    })
    with pytest.raises(task_service.ConflictError):
        task_service.update_task("owner", "t1", TaskUpdate(date="2026-10-14"))
    reference.update.assert_not_called()


def test_partial_time_update_cannot_shorten_below_15_minutes(stored_task, monkeypatch):
    reference, _ = stored_task
    monkeypatch.setattr(task_service, "check_time_conflict", lambda *a, **k: None)
    with pytest.raises(ValueError):
        task_service.update_task("owner", "t1", TaskUpdate(start_time="09:50"))
    reference.update.assert_not_called()


def test_complete_rejects_wrong_owner(stored_task):
    reference, snapshot = stored_task
    snapshot.to_dict.return_value["uid"] = "someone_else"
    with pytest.raises(ValueError, match="Unauthorized"):
        task_service.complete_task("owner", "t1")
    reference.update.assert_not_called()


def test_serialization_includes_explicit_utc_offset(stored_task):
    _, snapshot = stored_task
    serialized = task_service.serialize_task(snapshot)
    assert serialized["created_at"].endswith("+00:00")
    json.dumps(serialized)
