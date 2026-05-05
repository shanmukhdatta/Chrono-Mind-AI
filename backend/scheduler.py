import logging
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)
from apscheduler.triggers.cron import CronTrigger
from agents.rescheduler import run_for_all_users
import pytz

scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the background scheduler with nightly rescheduling job at IST 23:55"""
    ist = pytz.timezone('Asia/Kolkata')
    
    scheduler.add_job(
        run_for_all_users,
        trigger=CronTrigger(hour=23, minute=55, timezone=ist),
        id='nightly_reschedule',
        replace_existing=True,
        misfire_grace_time=3600  # Allow 1 hour grace period for server restarts
    )

    scheduler.start()
    logger.info("APScheduler started — nightly rescheduling at 23:55 IST")

def stop_scheduler():
    """Stop the scheduler cleanly"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler stopped")
