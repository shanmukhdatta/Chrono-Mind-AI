# ChronoMind V2 — Phase 1 manual browser acceptance

**Status:** checklist prepared; interactive browser clicks and results **not yet reported/verified**. Use branch `v2/phase1-foundation` and a dedicated non-production Firebase test project/account. Never paste passwords, Firebase service-account private keys, ID tokens or screenshots showing private information into PRs/chat.

## Setup (Windows/Antigravity)

1. Ensure the Phase 1 branch is current and has no unintended local edits: `git fetch origin`, `git status`, then `git merge --ff-only origin/v2/phase1-foundation`.
2. Run backend with `CHRONOMIND_DISABLE_LEGACY_SCHEDULER=1`, configured test Firebase Admin credentials, and CORS allowing `http://127.0.0.1:5173` **if using that exact browser origin**.
3. Run frontend with test project `VITE_FIREBASE_*` web settings and `VITE_API_URL=http://127.0.0.1:8000`. Confirm Google as an enabled provider and `127.0.0.1`/localhost authorized as required by Firebase Auth project settings.
4. Launch the Vite app, usually `http://127.0.0.1:5173`. Confirm API `http://127.0.0.1:8000/health` returns `status: ok` before interacting.

## Manual interaction checks

| Step | Real UI action | Expected result | Actual result |
| --- | --- | --- | --- |
| 1 | Open landing page; inspect Chrome Console and Network tabs | Page renders; no unhandled JavaScript errors | **PENDING** |
| 2 | Press **Sign In** / **Sign in with Google** | Google OAuth popup opens; approved test Google account logs in; redirects to `/dashboard` | **PENDING** |
| 3 | Click **Add Task**, create a non-production task for today's local date | Task card appears; POST succeeds; refreshing retains the task | **PENDING** |
| 4 | Create a second overlapping task on the same date | Conflict toast; backend responds 409; no duplicate created | **PENDING** |
| 5 | Edit original task title via card and press **Save Changes** | PATCH succeeds; title updates and survives refresh | **PENDING** |
| 6 | Mark task complete using task card | Completion changes UI and stats; survives refresh | **PENDING** |
| 7 | Open **Calendar**, switch day/week/month, navigate earlier/later dates | Calendar queries succeed and show dates/tasks consistently, without Firestore index errors | **PENDING** |
| 8 | Delete test task, accept confirmation dialog | Task disappears; remains absent after refresh | **PENDING** |
| 9 | Open Profile and sign out | Auth state cleared; protected routes redirect to landing page | **PENDING** |

**Important: the current frontend uses `signInWithPopup(auth, googleProvider)` in `frontend/src/hooks/useAuth.js`. There is no email/password sign-in form.** The previous Antigravity browser guide that instructed typing an email and password was incorrect; do not use it as acceptance evidence. An email/password test account can still be used separately by an API harness if the test Firebase project permits that method.

## Report back

Record the exact tested commit, browser version, which steps were performed, the visible result, and redacted Console/Network errors. Do not mark any pending steps passed simply because `npm run build` or API HTTP tests succeeded. Interactive UI testing **does not** prove concurrent task-write safety, Firebase token revocation integration or distributed leases. Those require separate integration tests.
