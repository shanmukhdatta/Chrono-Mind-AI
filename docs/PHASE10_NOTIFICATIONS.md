# V2 in-app deadline notifications

Authenticated endpoints:
- GET /api/v2/notifications?unread_only=false&limit=40
- GET /api/v2/notifications/unread-count
- POST /api/v2/notifications/{notification_id}/read
- POST /api/v2/notifications/mark-all-read

Notifications are stored user-scoped in PostgreSQL. Each user/local-day/task/category combination gets at most one notification. Deadline warnings distinguish upcoming deadlines within the local day from overdue tasks. The worker locks the owner row and has a unique constraint on (owner_uid,dedupe_key) to protect concurrent runs. Completed/archived tasks are never alerted.

**Worker separation:** Do not start this job in FastAPI lifespan or each Gunicorn worker. The operator-only script `python -m scripts.generate_v2_notifications --uid ...` is dry-run by default; write mode requires `CHRONOMIND_NOTIFICATIONS_JOB_ENABLED=1` and `--apply`. A managed scheduler/cron can invoke it once per period after live staging verification.

No mobile push, browser push, email delivery or background queue is claimed. Users see in-app notifications only after the external job runs. Test timezone boundaries, idempotence and API ownership against real Postgres in Antigravity before production rollout.
