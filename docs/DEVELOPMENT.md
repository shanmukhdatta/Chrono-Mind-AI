# ChronoMind AI — Reproducible Local Development

## Preconditions

- Windows PowerShell or equivalent terminal, Git, Python **3.11**, Node **20**, npm.
- Firebase project with Google sign-in configured, a private service account JSON, and browser Firebase web configuration.
- An optional Groq API key for the assistant; the backend should start without Groq but chat will fail gracefully.
- No credentials or actual user data in git, screenshots, bug reports or shared logs.

## Get the Phase 0 branch

```powershell
git clone https://github.com/shanmukhdatta/Chrono-Mind-AI.git
cd Chrono-Mind-AI
git fetch origin
git switch v2/phase0-safety
git pull --ff-only origin v2/phase0-safety
```

## Backend (PowerShell)

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` privately with your own values; service account file path should point to an actual readable key JSON file **outside the repository**. Phase 1 loads `backend/.env` during backend configuration initialization (existing process environment variables take precedence). For explicit PowerShell configuration, set environment variables as follows:

```powershell
$env:FIREBASE_SERVICE_ACCOUNT_PATH = "C:\path\outside\repo\firebase-service-account.json"
$env:CORS_ORIGINS = "http://localhost:5173"
$env:CHRONOMIND_DISABLE_LEGACY_SCHEDULER = "1"
# Optional privileged UID, only if testing authorized admin:
# $env:ADMIN_UID = "<your actual Firebase UID>"
# Optional AI chat:
# $env:GROQ_API_KEY = "<your Groq key>"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Expected: Uvicorn listening on localhost. In a second terminal, verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected JSON includes `status: ok`. Do not invoke the real nightly job on production accounts during Phase 0 testing. Scheduler is disabled in local testing via the environment variable above.

## Backend tests (inside backend)

```powershell
python -m pytest -q
python -m compileall -q .
```

Expected: pytest reports passing tests. If there are failures, share the full traceback with secrets redacted. Smoke tests override Firebase dependency; they do not prove a real Firebase deployment.

## Frontend (separate terminal at repo root)

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
```

Populate `VITE_API_URL=http://localhost:8000` and the six `VITE_FIREBASE_*` web configuration entries from your Firebase app. These browser settings are different from the service account private key.

```powershell
npm run build
npm run dev -- --host 127.0.0.1
```

Expected: Vite reports local address, typically `http://localhost:5173`. Test login and task CRUD only in a test Firebase project. Demo mode uses local illustrative tasks, **not authenticated production data**.

## Phase 0 manual checklist

1. Sign in with a test Firebase user; verify valid token accepted and absent/invalid token returns 401.
2. Confirm default/unset `ADMIN_UID` returns 403 for protected admin route.
3. POST a test task and GET by date; timestamp fields must be JSON and timezone-aware.
4. PATCH to an occupied **date only**, leaving times unchanged; expect 409.
5. PATCH duration below 15 minutes; expect 422 request validation or 400 merged-field validation.
6. Verify missing recurrence generation is clearly disclosed rather than assumed working.
7. With test data, verify no missed optional task is deleted and no two rollover placements overlap.
8. Inspect GitHub Actions results and attach redacted errors to PR #1.

### Known testing boundaries

Running `pytest` alone cannot validate live Firebase credentials, network-dependent LLM behavior, browser integrations or multi-instance concurrency. Those must be separately demonstrated in a test environment.

## Phase 1 automated quality gates

Run `python -m pytest -q` in `backend/`, plus `npm test` and `npm run build` in `frontend/`. The new GitHub Actions workflow `.github/workflows/phase1-quality.yml` runs these checks on the Phase 1 branch and on PRs to Phase 0/main. Frontend tests pin `TZ=Asia/Kolkata` to exercise calendar-day boundaries. These checks do not replace the separate Firebase emulator and Antigravity test-account checks pending from Phase 0.
