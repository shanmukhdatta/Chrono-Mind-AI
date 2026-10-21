"""Operator-only proactive replan worker for missed and overdue work.

Finds accounts with unfinished work that is overdue or whose scheduled sessions
are all in the past, then creates the same validated, human-review proposal the
authenticated /api/v2/planning/replan endpoint creates. Nothing is committed
without the user approving the proposal in Approvals.

Runs as a managed cron/scheduler job (Render Cron or equivalent), never inside
a FastAPI request. Dry-run is the default.

  cd backend
  python -m scripts.propose_v2_replans --uid <firebase-uid>            # dry run
  CHRONOMIND_REPLAN_JOB_ENABLED=1 python -m scripts.propose_v2_replans \
      --uid <firebase-uid> --apply
  CHRONOMIND_REPLAN_JOB_ENABLED=1 python -m scripts.propose_v2_replans \
      --all-users --apply
"""
import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from v2.db import engine
from v2.models import ScheduleBlock, Task, User
from v2.planning_api import create_replan_proposal

# Do not create more than one proposal per account within this window.
PROPOSAL_COOLDOWN = timedelta(hours=12)


def _aware(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def needs_replan(db: Session, uid: str, now: datetime) -> tuple[bool, str]:
    """Decide whether this account has unfinished work worth re-proposing."""
    pending = db.scalars(select(Task).where(
        Task.owner_uid == uid, Task.status == "pending"
    )).all()
    if not pending:
        return False, "no pending tasks"

    overdue = any(
        task.deadline_at is not None and _aware(task.deadline_at) < now
        for task in pending
    )
    if overdue:
        return True, "overdue deadline"

    scheduled_task_ids = {task.id for task in pending}
    blocks = []
    if scheduled_task_ids:
        blocks = db.scalars(select(ScheduleBlock).where(
            ScheduleBlock.owner_uid == uid,
            ScheduleBlock.task_id.in_(scheduled_task_ids),
        )).all()
    if blocks:
        planned = {block.task_id for block in blocks}
        future_planned = {
            block.task_id for block in blocks if _aware(block.ends_at) > now
        }
        # Work that had sessions booked only in the past is unfinished missed work.
        missed = planned - future_planned
        if missed and len(planned) == len(missed):
            return True, "all sessions for pending work are in the past"
        return False, "current schedule still covers pending work"
    return True, "pending work has no scheduled sessions"


def inside_cooldown(db: Session, uid: str, now: datetime) -> bool:
    from v2.models import PlanProposal
    cutoff = now - PROPOSAL_COOLDOWN
    recent = db.scalar(select(PlanProposal.id).where(
        PlanProposal.owner_uid == uid, PlanProposal.created_at >= cutoff
    ).limit(1))
    return recent is not None


def main():
    parser = argparse.ArgumentParser(description="ChronoMind V2 proactive replan worker")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--uid", help="Single authorized Firebase UID")
    target.add_argument("--all-users", action="store_true", help="Scan every account")
    parser.add_argument("--days", type=int, default=7, help="Planning horizon 1..14 (default 7)")
    parser.add_argument("--apply", action="store_true", help="Create proposals and notifications")
    args = parser.parse_args()

    if not 1 <= args.days <= 14:
        parser.error("--days must be between 1 and 14")
    if args.apply and os.getenv("CHRONOMIND_REPLAN_JOB_ENABLED") != "1":
        parser.error("CHRONOMIND_REPLAN_JOB_ENABLED=1 required for --apply")

    now = datetime.now(timezone.utc)
    with Session(engine()) as db:
        if args.all_users:
            uids = list(db.scalars(select(User.uid).order_by(User.uid)).all())
            db.rollback()
        else:
            uids = [args.uid]

        print(f"Proactive replan worker: accounts={len(uids)}, horizon={args.days}d, apply={args.apply}")
        if not args.apply:
            print("DRY RUN: no PostgreSQL writes will be performed.")

        created = 0
        skipped = 0
        for uid in uids:
            eligible, reason = needs_replan(db, uid, now)
            if not eligible:
                skipped += 1
                continue
            if args.apply and inside_cooldown(db, uid, now):
                skipped += 1
                continue
            print(f"  {uid}: {'WOULD REPLAN' if not args.apply else 'REPLANNING'} ({reason})")
            if not args.apply:
                continue
            with db.begin():
                result = create_replan_proposal(
                    db, uid, args.days, trigger="missed_task_recovery", notify=True
                )
                if result["proposal_id"] is not None:
                    created += 1

        print(f"Summary: replan candidates={len(uids) - skipped}, skipped={skipped}, proposals created={created}")
        if not args.apply:
            print("Dry run completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
