"""Legacy APScheduler with Firestore-backed cross-worker run claims.

Each Gunicorn process may register the trigger, but only one process can claim
each IST day's job. A dedicated job worker replaces this in V2 Phase 10.
"""
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from firebase_admin import firestore

from agents.rescheduler import run_for_all_users
from services.firebase_service import get_db

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")
_scheduler = None


def _claim_run(job_ref, token, now):
    """Transactional compare-and-set; only one worker claims a given date."""
    transaction = get_db().transaction()

    @firestore.transactional
    def attempt(tx):
        snapshot = job_ref.get(transaction=tx)
        if snapshot.exists:
            current = snapshot.to_dict()
            if current.get("status") == "completed":
                return False
            lease_until = current.get("lease_until")
            if (current.get("status") == "running" and
                    lease_until is not None and lease_until > now):
                return False
        tx.set(job_ref, {
            "status": "running",
            "token": token,
            "claimed_at": now,
            "lease_until": now + timedelta(hours=8),
        })
        return True

    return attempt(transaction)


def _finish_run(job_ref, token, successful, summary):
    """Update only a claim we still own, avoiding stale-run overwrites."""
    transaction = get_db().transaction()

    @firestore.transactional
    def finish(tx):
        snapshot = job_ref.get(transaction=tx)
        if not snapshot.exists or snapshot.to_dict().get("token") != token:
            return False
        tx.update(job_ref, {
            "status": "completed" if successful else "failed",
            "finished_at": datetime.now(timezone.utc),
            "summary": summary,
        })
        return True

    return finish(transaction)


def run_nightly_once():
    """Run at most once per IST date across API workers; retry failed runs."""
    now = datetime.now(timezone.utc)
    date_key = now.astimezone(IST).date().isoformat()
    job_ref = get_db().collection("_chronomind_jobs").document("nightly-" + date_key)
    token = str(uuid.uuid4())
    if not _claim_run(job_ref, token, now):
        logger.info("Nightly rollover already claimed or finished for %s", date_key)
        return {"skipped": True}

    try:
        summary = run_for_all_users()
        successful = summary["errors"] == 0
        _finish_run(job_ref, token, successful, summary)
        if not successful:
            logger.warning("Rollover completed with issues: %s", summary)
        return summary
    except Exception as exc:
        logger.exception("Nightly rollover failed")
        _finish_run(job_ref, token, False, {"error_type": type(exc).__name__})
        raise


def start_scheduler():
    """Register one logical nightly job even when multiple web workers exist."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return
    if os.getenv("CHRONOMIND_DISABLE_LEGACY_SCHEDULER") == "1":
        logger.warning("Legacy nightly scheduler is disabled by configuration")
        return
    scheduler = BackgroundScheduler(timezone=IST)
    scheduler.add_job(
        run_nightly_once,
        trigger=CronTrigger(hour=23, minute=55, timezone=IST),
        id="nightly_reschedule",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Nightly scheduler running at 23:55 Asia/Kolkata with Firestore run claims")


def stop_scheduler():
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
