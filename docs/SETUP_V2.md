# ChronoMind AI V2 — Resume & local integration guide

This is the **canonical setup checklist** when resuming the prototype after a break.

## 0. Get the code

Clone [the repository](https://github.com/shanmukhdatta/Chrono-Mind-AI). Check the active PR and merge status before selecting `main`:

```powershell
git clone https://github.com/shanmukhdatta/Chrono-Mind-AI.git
cd Chrono-Mind-AI
git checkout main
git pull --ff-only origin main
git rev-parse HEAD
```

Use Python 3.11+, Node 20+, npm, PostgreSQL 16 (or equivalent tested version), a Firebase **test** project with Google Auth and, optionally, a Groq key. Do not put tokens or service-account files in Git.

## 1. Backend environment

```powershell
cd backend
Copy-Item .env.example .env
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Edit **backend/.env** locally:
- `DATABASE_URL`: local PostgreSQL database, e.g. `postgresql+psycopg://chronomind:LOCAL_PASSWORD@localhost:5432/chronomind`.
- `FIREBASE_SERVICE_ACCOUNT_PATH`: your local Admin SDK private JSON file, or use `FIREBASE_SERVICE_ACCOUNT_JSON` from a secure secret store.
- `GROQ_API_KEY`: optional; leave blank for deterministic scheduling and fallback assistant.
- `CORS_ORIGINS=http://localhost:5173`.
- `CHRONOMIND_DISABLE_LEGACY_SCHEDULER=1`; `LANGGRAPH_STRICT_MSGPACK=true`.
- Never set `CHRONOMIND_*_JOB_ENABLED` to 1 until manually tested.

`backend/api.env.example` is a descriptive alias; **backend/.env is the file used at runtime**. Alembic and the V2 database module load the environment without overriding shell variables.

## 2. Run disposable PostgreSQL and migrations

From the repository root:

```powershell
docker compose -f compose.v2.yaml up -d
cd backend
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m scripts.init_langgraph_checkpoints
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

The local database password in `backend/.env` must agree with `compose.v2.yaml`. Initialization does **not** happen automatically on API startup. Verify `GET http://localhost:8000/health/v2` returns a ready status before using V2 pages.

## 3. Frontend environment

In a second terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Fill in the **Firebase web config** from your Firebase test project and set `VITE_API_URL=http://localhost:8000` and `VITE_V2_DEFAULT=true`. Enable Google Sign-In and authorize `localhost` in Firebase Authentication. `VITE_*` is browser-visible: **never** put Groq, PostgreSQL credentials or Admin JSON there.

Sign in with Google/Firebase to test V2 persistence. The route `/demo` is an explicit **read-only UI example**, requiring no account and writing no data.

## 4. Optional realistic demo fixtures (LOCAL ONLY)

Create/use a *dedicated Firebase test account* and take its UID from Firebase Console. `--uid` associates the demo rows with that test account; it does not bypass authentication.

```powershell
cd backend
.\.venv\Scripts\python.exe -m scripts.seed_v2_demo --uid YOUR_TEST_UID
```

Dry-run output does not touch the database. For actual **localhost** seeding after reviewing the DB:

```powershell
# Set CHRONOMIND_DEMO_SEED_ENABLED=1 privately in backend/.env
.\.venv\Scripts\python.exe -m scripts.seed_v2_demo --uid YOUR_TEST_UID --apply
```

Fixture IDs are deterministic: repeat execution does not duplicate rows. The script refuses non-local hosts, production/staging environments and accidental writes without explicit opt-in. Use a disposable DB; never seed a real user's account.

## 5. Testing and evidence

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q v2
cd ..\frontend
npm test
npm run build
```

Then perform **real browser acceptance**: Firebase login; task/goal CRUD; parent/child and dependency validation; calendar fixed events; recurrence; plan preview; approve/reject/undo; agent interrupt/resume after restarting backend; assistant with valid Groq and without a key; voice; focus; notification generation; two-user isolation. Save timestamped logs and SHA, redact secrets. GitHub CI also runs disposable PostgreSQL migration/checkpoint integration. A passing CI run is not proof that your own Firebase/Groq/browser/Render config works.

## 6. Production or old Firestore data — NOT part of local demo

- Do not auto-import Firestore users or enable live jobs without backups, reconciliation and approval.
- Use the existing `scripts.import_firestore_tasks` dry run before any authorized V1→V2 migration.
- Account purge does not delete Firebase Auth identity, and external store cleanup can fail; check the returned cleanup report.
- Deployment configs are present, but production staging, observability, jobs and rollback remain independent acceptance tasks.

When resuming, start with [FINAL_HANDOFF.md](FINAL_HANDOFF.md) and [FEATURE_MAP.md](FEATURE_MAP.md).
