"""Background recurrence expansion worker.

Materializes upcoming tasks for active recurrence series without manual UI clicks.
Runs as a scheduled operator job or periodic worker.
"""
import argparse
import os
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from v2.db import engine
from v2.models import RecurrenceSeries, User
from v2.recurrence import materialize_series_occurrences


def main():
    parser = argparse.ArgumentParser(description="ChronoMind V2 Recurrence Expansion Worker")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--uid", help="Single verified Firebase UID")
    target.add_argument("--all-users", action="store_true", help="Expand recurring series across all active users")
    parser.add_argument("--days", type=int, default=14, help="Horizon days to materialize ahead (1..90, default 14)")
    parser.add_argument("--apply", action="store_true", help="Commit materialized tasks to PostgreSQL")
    args = parser.parse_args()

    if not 1 <= args.days <= 90:
        parser.error("--days must be between 1 and 90")

    if args.apply and args.all_users and os.getenv("CHRONOMIND_RECURRENCE_JOB_ENABLED") != "1":
        parser.error("Bulk recurrence write job requires CHRONOMIND_RECURRENCE_JOB_ENABLED=1")

    with Session(engine()) as db:
        if args.all_users:
            uids = list(db.scalars(select(User.uid).order_by(User.uid)).all())
        else:
            uids = [args.uid]

        print(f"Recurrence expansion worker: users={len(uids)}, horizon={args.days}d, apply={args.apply}")
        if not args.apply:
            print("DRY RUN: no tasks will be committed to PostgreSQL.")

        total_created = 0
        total_series = 0
        for uid in uids:
            with db.begin():
                db.scalar(select(User).where(User.uid == uid).with_for_update())
                series_list = db.scalars(
                    select(RecurrenceSeries).where(RecurrenceSeries.owner_uid == uid, RecurrenceSeries.active == True)
                ).all()
                total_series += len(series_list)
                for series in series_list:
                    if args.apply:
                        created, _, _ = materialize_series_occurrences(db, uid, series, args.days)
                        total_created += created

        print(f"Summary: processed {total_series} series across {len(uids)} user(s).")
        if args.apply:
            print(f"Committed {total_created} new recurring task instance(s).")
        else:
            print("Dry run completed successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
