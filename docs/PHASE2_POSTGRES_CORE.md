# Phase 2 — PostgreSQL domain foundation (review required)

This feature branch adds **real API-backed SQLAlchemy models** for user-owned goals, logical tasks, schedule blocks, fixed events and preferences. V2 endpoints are `/api/v2/goals`, `/api/v2/tasks`, and `/api/v2/preferences`.

## Safety boundaries
- Existing V1 endpoints continue using Firestore; **no automatic Firestore migration or cutover**.
- All V2 endpoints use the verified Firebase `uid`, never a client-submitted owner ID.
- No connection occurs until a V2 endpoint is requested; no automatic schema creation on startup.
- A V2 request without `DATABASE_URL` returns a configuration error, not a fake response.
- Goal deletion unlinks tasks; it does not delete tasks. Task updates enforce optimistic `version` checking.
- No claim of live Postgres verification until credentials, migration, and integration run are checked.

## Development setup

Set `DATABASE_URL` using a local secret or secure environment variable, e.g. a **local-only** PostgreSQL URL `postgresql+psycopg://chronomind:password@localhost:5432/chronomind`. Do not commit credentials.

```bash
cd backend
python -m pip install -r requirements.txt
python -m alembic -c alembic.ini upgrade head
CHRONOMIND_DISABLE_LEGACY_SCHEDULER=1 python -m uvicorn main:app --reload
python -m pytest -q
```

On Windows PowerShell set environment variables with `$env:DATABASE_URL = '...'` and `$env:CHRONOMIND_DISABLE_LEGACY_SCHEDULER = '1'` before running commands.

## Manual verification
- Firebase-authenticated create/list/update goals and create/list/update tasks.
- Verify users cannot read, link, or update one another's records.
- Edit the same task twice with an old `version`; second request must return HTTP 409.
- Delete a goal; linked tasks must remain with `goal_id = null`.
- Refresh and reconnect; data must remain in PostgreSQL.
- Existing Firestore dashboard must still run unchanged.

## Phase 2 still remaining
Provisioning, production Postgres integration, safe Firestore export/backfill/reconciliation, recurrence migration, backup/restore, deletion/export, live cutover decision, and deployment configuration. Other phases (planning, LangGraph, approvals, voice, insights, full frontend) are not implemented by this branch.
