"""Migration is idempotent and does not confuse scheduled time with deadline."""
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from v2.legacy_import import convert_legacy_task, import_converted
from v2.models import Base, LegacyTaskArchive, ScheduleBlock, Task


def record(title="Study", start="09:00", end="10:00"):
    return {"title": title, "date": "2026-10-20", "start_time": start,
            "end_time": end, "importance": "important", "completed": False}


def test_source_mapping_preserves_session_but_not_false_deadline():
    item = convert_legacy_task("alice", "firestore-1", record(), "Asia/Kolkata")
    assert item.task_data["deadline_at"] is None
    assert item.task_data["legacy_id"] == "firestore-1"
    assert item.starts_at == datetime(2026, 10, 20, 3, 30, tzinfo=timezone.utc)
    assert item.ends_at == datetime(2026, 10, 20, 4, 30, tzinfo=timezone.utc)


def test_malformed_v1_task_fails_closed():
    import pytest
    with pytest.raises(ValueError):
        convert_legacy_task("alice","bad",record(start="12:00",end="10:00"),"Asia/Kolkata")
    with pytest.raises(ValueError):
        convert_legacy_task("alice","empty",record(title=" "), "Asia/Kolkata")


def test_backfill_repeat_does_not_duplicate_and_conflicts_do_not_delete():
    engine = create_engine("sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    try:
        source = convert_legacy_task("alice", "src1", record(), "Asia/Kolkata")
        colliding = convert_legacy_task("alice", "src2", record(title="Class"), "Asia/Kolkata")
        with Session(engine) as db:
            assert import_converted(db, source) == "imported"
            db.commit()
            assert import_converted(db, source) == "already_present"
            assert import_converted(db, colliding) == "imported_unscheduled"
            db.commit()
            assert db.query(Task).filter(Task.owner_uid == "alice").count() == 2
            assert db.query(ScheduleBlock).count() == 1
            assert db.query(LegacyTaskArchive).count() == 2
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()
