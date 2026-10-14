"""Safe operator-only notification worker. Never launched by FastAPI workers."""
import argparse
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from v2.db import engine
from v2.models import User
from v2.notifications_api import create_daily_notifications


def main():
    parser = argparse.ArgumentParser()
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--uid", help="Single authorized Firebase UID")
    choice.add_argument("--all-users", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply and os.getenv("CHRONOMIND_NOTIFICATIONS_JOB_ENABLED") != "1":
        parser.error("CHRONOMIND_NOTIFICATIONS_JOB_ENABLED=1 required for writes")
    if args.all_users and os.getenv("CHRONOMIND_NOTIFICATIONS_JOB_ENABLED") != "1":
        parser.error("Bulk account access requires explicit operator enablement")
    with Session(engine()) as db:
        if args.all_users:
            uids = list(db.scalars(select(User.uid).order_by(User.uid)).all())
            # Release read transaction before opening per-user write transactions.
            db.rollback()
        else:
            uids = [args.uid]
        print(f"V2 notification run: accounts={len(uids)}, apply={args.apply}")
        if not args.apply:
            print("DRY RUN: no PostgreSQL or Firebase writes")
            return 0
        created = 0
        for uid in uids:
            with db.begin():
                created += create_daily_notifications(db, uid, datetime.now(timezone.utc))
        print(f"In-app notifications created: {created}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
