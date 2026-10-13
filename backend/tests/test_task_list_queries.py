"""Firestore list query regressions: do not require composite indexes."""
from unittest.mock import MagicMock

import pytest

from services import task_service


class QueryRecorder:
    def __init__(self, documents):
        self.documents = documents
        self.operations = []

    def where(self, field, op, value):
        self.operations.append(("where", field, op, value))
        return self

    def order_by(self, field):
        self.operations.append(("order_by", field))
        return self

    def get(self):
        return self.documents


def document(task_id, day, clock, completed=False):
    snapshot = MagicMock()
    snapshot.id = task_id
    snapshot.to_dict.return_value = {
        "date": day, "start_time": clock, "completed": completed,
        "title": f"Task {task_id}",
    }
    return snapshot


@pytest.fixture
def wire_query(monkeypatch):
    def arrange(documents):
        query = QueryRecorder(documents)
        db = MagicMock()
        db.collection.return_value.document.return_value.collection.return_value = query
        monkeypatch.setattr(task_service, "get_db", lambda: db)
        return query
    return arrange


def test_day_list_avoids_composite_order_and_sorts_filtered_tasks(wire_query):
    query = wire_query([
        document("late", "2026-10-14", "15:00"),
        document("done", "2026-10-14", "12:00", completed=True),
        document("early", "2026-10-14", "09:00"),
    ])
    result = task_service.get_tasks("owner", date="2026-10-14", status="incomplete")
    assert [t["task_id"] for t in result] == ["early", "late"]
    assert query.operations == [("where", "date", "==", "2026-10-14")]


def test_date_range_uses_single_field_index_and_stable_order(wire_query):
    query = wire_query([
        document("next", "2026-10-15", "08:00"),
        document("z", "2026-10-14", "17:00"),
        document("b", "2026-10-14", "09:00"),
        document("a", "2026-10-14", "09:00"),
    ])
    result = task_service.get_tasks_range(
        "owner", "2026-10-14", "2026-10-15"
    )
    assert [t["task_id"] for t in result] == ["a", "b", "z", "next"]
    assert query.operations == [
        ("where", "date", ">=", "2026-10-14"),
        ("where", "date", "<=", "2026-10-15"),
        ("order_by", "date"),
    ]


def test_unfiltered_list_retains_original_server_side_ordering(wire_query):
    query = wire_query([document("first", "2026-10-14", "09:00")])
    assert [t["task_id"] for t in task_service.get_tasks("owner")] == ["first"]
    assert query.operations == [("order_by", "start_time")]
