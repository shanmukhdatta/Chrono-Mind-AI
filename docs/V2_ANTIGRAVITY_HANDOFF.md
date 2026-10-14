# ChronoMind AI V2 — Local integration acceptance (Antigravity / Windows)

**Branch to inspect after PR #39 is merged:** `main`. The release-hardening branch was created from main. Legacy Firestore migration and production deployment have NOT been performed. Run actual integration tests before claiming deployment readiness.

## 1. Clone and choose the integrated branch

```powershell
git clone https://github.com/shanmukhdatta/Chrono-Mind-AI.git
cd Chrono-Mind-AI
git fetch origin
git switch main
git pull --ff-only origin main
git status --short
git rev-parse HEAD
```

If already cloned: `git fetch origin; git switch main; git pull --ff-only origin main`. Working tree should be clean.

## 2. Backend: isolated tests before configuring secrets

Requires Python 3.11, Node 20+, npm and optionally local PostgreSQL 16+. 

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:CHRONOMIND_DISABLE_LEGACY_SCHEDULER = '1'
.\.venv\Scripts\python.exe -m compileall -q .
.\.venv\Scripts\python.exe -m pytest -q
```

All isolated regressions must pass, including registered routes and migration-chain checks. If any test fails, **do not merge**, and return the full traceback and commit SHA.

## 3. Frontend: tests and production build

```powershell
cd ..\frontend
npm ci
npm test
npm run build
```

No incomplete UI should be presented as operational. Set private frontend Firebase config in `frontend/.env.local` from the example; never commit it.

## 4. PostgreSQL and Firebase setup

Use a throwaway/local PostgreSQL database for integration, not production. From the repository root start the bundled local database with `docker compose -f compose.v2.yaml up -d` (Docker Desktop required). Put `DATABASE_URL` in your *private shell/environment*, for example a local-only `postgresql+psycopg://USER:LOCAL_PASSWORD@localhost:5432/chronomind`. Set Firebase Admin credentials as described in `backend/.env.example` using private local files or an authorized service connection. Set `CORS_ORIGINS=http://localhost:5173`. Do not commit or paste actual credentials into chat.

```powershell
cd ..\backend
$env:DATABASE_URL = 'postgresql+psycopg://USER:LOCAL_PASSWORD@localhost:5432/chronomind'
$env:CHRONOMIND_DISABLE_LEGACY_SCHEDULER = '1'
$env:LANGGRAPH_STRICT_MSGPACK = 'true'
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m scripts.init_langgraph_checkpoints
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Start frontend in another Antigravity terminal (`cd frontend; npm run dev`), with `VITE_API_URL=http://localhost:8000` and correct Firebase frontend variables. Sign in with **Google/Firebase**, not an invented username-password flow.

## 5. End-to-end browser acceptance

Check each operation with an actual logged-in Firebase user and refresh the browser afterward. All writes must persist in the local PostgreSQL instance.

1. **V2 Dashboard**: `/dashboard-v2` displays real counts, priorities and no fake user metrics.
2. **Tasks**: `/tasks-v2` create, edit, complete, reopen, archive, set timezone-aware deadline; stale version returns 409.
3. **Goals**: `/goals` create/edit/status changes, link new tasks, delete goal without deleting linked tasks.
4. **Preferences**: `/preferences` update timezone, working hours and limits; refresh and confirm persistence.
5. **Calendar**: `/calendar-v2` create fixed commitment, reject overlap (409), edit, delete.
6. **Recurrence**: `/recurrence-v2` create weekly/daily series, materialize twice (no duplicates), pause/resume and safe skip.
7. **Planning**: `/planning` preview scheduled blocks and unscheduled explanations, verify no database mutation before confirmation.
8. **Approvals**: `/approvals` create proposal, approve (persist blocks), reject separate proposal, undo unchanged approved blocks.
9. **Agent**: POST `/api/v2/agent/runs`, restart FastAPI, GET run from saved checkpoint, approve corresponding plan, POST resume.
10. **Assistant**: `/assistant-v2` create a task/goal *draft*, do not save without explicit click; test real Groq or truthful fallback. Try microphone permissions, speech availability and typed fallback.
11. **Focus**: `/focus-v2` start, browser reload, finish, verify server-based duration; consent off by default, enable and disable, verify event history is cleared.
12. **Notifications**: run external job in an enabled test environment, refresh `/notifications-v2`, mark unread/read and rerun job without duplicates.
13. **Privacy**: Profile export downloads only this user's V2 SQL data, and legacy Delete button accurately explains its limited scope.
14. **Isolation**: Second Firebase test account must not access any first-user object via manipulated IDs.
15. **Resilience**: Temporarily unset the Groq key and confirm normal task/calendar/planning CRUD remains functional.

## 6. Source migration is explicitly gated

The Firestore importer is dry-run by default. Never use `--apply` without a verified Firestore backup, source/target count reconciliation, reviewed timezone interpretation and explicit migration flag. It does not delete Firestore or automatically cut over frontend traffic.

## 7. Operator jobs are separate from web workers

Only an authorized, independently scheduled cron/worker should run `python -m scripts.generate_v2_notifications --all-users --apply` with `CHRONOMIND_NOTIFICATIONS_JOB_ENABLED=1` after local tests. No email/mobile push is implemented. Recurrence expansion also requires a scheduled worker not yet deployed.

## 8. What is still not signed off

Production PostgreSQL migrations, full Firestore subcollection migration, Firebase+PostgreSQL end-to-end user isolation, distributed races/locks, checkpoint recovery, browser voice support, complete account deletion including LangGraph/Firebase stores, advanced recurrence/dependency scheduling, managed cron deployment, accessibility/mobile E2E, monitoring/evaluations, staging rollback and actual public production verification are **pending**.

## 9. Return this evidence to the implementation chat

Paste the complete test output for backend pytest, frontend Vitest/build, Alembic, and any live API/UI failures. Include `git rev-parse HEAD`, `git status --short`, and the exact action/URL that failed. Redact all secrets and user data. Do not merge all stacked PRs at once merely because CI is green.

## 10. Additional acceptance after PR #39

- Apply **Alembic through revision 0011** and confirm database table/schema upgrades with actual local PostgreSQL. Confirm the `v2_schedule_blocks.source` column handles `plan:<uuid>` without truncation.
- Create a non-splittable task exceeding 90 minutes and verify the preview labels it unscheduled; create a splittable longer task and verify block generation.
- Validate task duration reductions cannot go below booked minutes; deadline edits conflicting with booked sessions return 409; task completion removes only future scheduled blocks.
- Generate and review a planning proposal; move a block in Approval Center and verify POST approval writes the revised schedule, while rejected/past/conflicting moves do not save.
- Inspect user-owned `GET /api/v2/plans/{id}/history` to confirm the before/after edit and approval reason codes. Test another account gets 404.
- Verify fast/reasoning/no-LLM assistant routing and `GET /api/v2/assistant/metrics`, with no Groq key as well as a valid test key. No raw messages should be stored in telemetry.
- Verify jobs never run in each web worker, and no failed scheduled tasks are silently deleted.
- Compare the **README feature audit** with actual code, and list missing/partial features separately from bugs. Implement missing core product functionality on new branches rather than claiming untested features pass.

## 11. Human-confirmed assistant task actions (PR #40)

- Sign into V2 using a real Firebase account and create a pending task with a recognizable name. In Assistant V2, ask it to rename/update, complete or archive that task. Confirm that /assistant/chat returns a *draft* and does not change the task automatically.
- Inspect the proposal's exact task ID and version; click the confirmation button and verify V2 Tasks refreshes with the expected persisted change.
- Test deletion explicitly on an unscheduled task; also test an already-scheduled task, which must be rejected with HTTP 409 rather than silently removing calendar blocks.
- From a second Firebase account, attempt to replay the first user's task ID and verify rejection. Edit the same task from another tab before confirming an old draft: stale version must return HTTP 409.
- Disconnect Groq and verify the assistant returns a truthful fallback with no writes; the normal manual Tasks and Goals screens must still work.
- The interpreter is NOT allowed to initiate arbitrary tools, URLs, calls, or calendar mutations. All task changes must use the known authenticated task CRUD endpoints after user confirmation.
