"""Firestore transactional job ownership behavior using in-memory doubles."""
from datetime import datetime, timedelta, timezone

from scheduler import _claim_run, _finish_run


class Snapshot:
    def __init__(self, content):
        self.content = content
        self.exists = content is not None

    def to_dict(self):
        return dict(self.content)


class Reference:
    def __init__(self):
        self.data = None

    def get(self, transaction=None):
        return Snapshot(self.data)


class Transaction:
    def set(self, reference, data):
        reference.data = dict(data)

    def update(self, reference, updates):
        reference.data.update(updates)


class Database:
    def transaction(self):
        return Transaction()


def test_claim_is_exclusive_and_completed_runs_stay_completed(monkeypatch):
    import scheduler
    monkeypatch.setattr(scheduler, "get_db", lambda: Database())
    monkeypatch.setattr(scheduler.firestore, "transactional", lambda fn: fn)
    ref = Reference()
    now = datetime(2026, 10, 13, tzinfo=timezone.utc)
    assert _claim_run(ref, "first", now)
    assert not _claim_run(ref, "second", now)
    assert not _finish_run(ref, "second", True, {})
    assert _finish_run(ref, "first", True, {"users": 1})
    assert not _claim_run(ref, "third", now + timedelta(hours=10))


def test_stale_claim_can_be_recovered(monkeypatch):
    import scheduler
    monkeypatch.setattr(scheduler, "get_db", lambda: Database())
    monkeypatch.setattr(scheduler.firestore, "transactional", lambda fn: fn)
    ref = Reference()
    now = datetime(2026, 10, 13, tzinfo=timezone.utc)
    assert _claim_run(ref, "old", now)
    assert _claim_run(ref, "new", now + timedelta(hours=9))
    assert not _finish_run(ref, "old", True, {})
    assert ref.data["token"] == "new"
