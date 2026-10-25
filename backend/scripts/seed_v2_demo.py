"""Local-only, opt-in sample records for a *test* Firebase UID.

Examples:
    python -m scripts.seed_v2_demo --uid YOUR_TEST_FIREBASE_UID
    CHRONOMIND_DEMO_SEED_ENABLED=1 python -m scripts.seed_v2_demo --uid YOUR_TEST_FIREBASE_UID --apply

Never bypass Firebase authentication and never modify remote databases with fixtures.
"""
import argparse
import os
import sys
from datetime import datetime, timedelta, time, timezone
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from v2.db import engine, get_or_create_user
from v2.models import FixedEvent, Goal, Task

SAMPLES = (
    ("DSA practice", 60, "placements"),
    ("Review experiment results", 45, "research"),
    ("Read instrumentation notes", 30, "academics"),
)


def fixture_id(uid: str, label: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"chronomind:v2:local-fixture:{uid}:{label}"))


def seed_local_demo(uid: str) -> dict:
    """Idempotently insert rows into a previously migrated localhost database."""
    zone = ZoneInfo("Asia/Kolkata")
    day = datetime.now(zone).date() + timedelta(days=1)
    due = datetime.combine(day, time(21, 0), zone).astimezone(timezone.utc)
    event_start = datetime.combine(day, time(9, 0), zone).astimezone(timezone.utc)
    event_end = datetime.combine(day, time(11, 0), zone).astimezone(timezone.utc)
    counts = {"goals": 0, "tasks": 0, "fixed_events": 0}
    with Session(engine()) as db:
        with db.begin():
            get_or_create_user(db, uid)
            goal_id = fixture_id(uid, "goal")
            if db.get(Goal, goal_id) is None:
                db.add(Goal(id=goal_id, owner_uid=uid, title="Sample: Complete this week's priorities",
                            description="Local-only test fixture for planning behavior"))
                counts["goals"] += 1
            for title, duration, tag in SAMPLES:
                task_id = fixture_id(uid, "task:" + tag)
                if db.get(Task, task_id) is None:
                    db.add(Task(
                        id=task_id, owner_uid=uid, goal_id=goal_id,
                        title="Sample: " + title, duration_minutes=duration,
                        context_tags=[tag], importance="important",
                        deadline_at=due,
                    ))
                    counts["tasks"] += 1
            event_id = fixture_id(uid, "event:lecture")
            if db.get(FixedEvent, event_id) is None:
                db.add(FixedEvent(id=event_id, owner_uid=uid, title="Sample: College lecture",
                                  starts_at=event_start, ends_at=event_end))
                counts["fixed_events"] += 1
    return counts


def main():
    parser = argparse.ArgumentParser(description="Seed LOCAL PostgreSQL only with non-sensitive sample tasks")
    parser.add_argument("--uid", required=True, help="UID of a dedicated test Firebase account")
    parser.add_argument("--apply", action="store_true", help="Allow writing to the local test database")
    args = parser.parse_args()
    if not args.uid.strip():
        parser.error("UID cannot be blank")
    if not args.apply:
        print("DRY RUN: 1 sample goal, 3 tasks and 1 fixed event; no database connection or writes")
        return 0
    if os.getenv("CHRONOMIND_DEMO_SEED_ENABLED") != "1":
        parser.error("Set CHRONOMIND_DEMO_SEED_ENABLED=1 to explicitly enable test fixture writes")
    url = os.getenv("DATABASE_URL", "")
    if not url:
        parser.error("DATABASE_URL required; configure a disposable PostgreSQL instance")
    host = make_url(url.replace("postgres://", "postgresql://", 1)).host
    if host not in ("localhost", "127.0.0.1", "::1"):
        parser.error("Demo fixture seeding is prohibited on non-local database hosts")
    if os.getenv("CHRONOMIND_ENVIRONMENT", "development").lower() in ("production", "staging"):
        parser.error("Demo fixtures are not permitted in production or staging")
    print("Local test fixture records created:", seed_local_demo(args.uid))
    return 0


if __name__ == "__main__":
    sys.exit(main())
