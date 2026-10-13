# Phase 1 — Development Foundation, Modularity and CI

**Development branch:** `v2/phase1-foundation` (forked from `v2/phase0-safety` at `5b7c99e7`).  
**Phase 0:** Draft PR #1 remains **unmerged and unapproved**. Phase 1 must not change `main`.

## Engineering decisions

- Retain the modular monolith and existing FastAPI router/service/model/agent modules and React page/hook/store/component separation. No new databases, queues, containers or mock production APIs.
- Introduce `backend/core/config.py` as the process-configuration boundary. `backend/.env` may be loaded locally by python-dotenv, while real environment variables win. Reject wildcard or malformed CORS origins with credentialed requests.
- Introduce `backend/core/lifecycle.py` for scheduler start/stop, including cleanup on abnormal shutdown. Maintain the Phase 0 Firestore-backed legacy lease; this is *not* a multi-worker emulator verification.
- Keep legacy backend entrypoint `uvicorn main:app`, existing API paths and scheduler-disable flag.
- Standardize browser local-date keys in `frontend/src/lib/date.js` and route dashboard/store usage through the tested function; do not change timezone/persistence formats.
- Add an explicit Phase 1 GitHub Actions workflow for Python 3.11 backend regressions and Node 20 frontend unit tests + production build. Existing Phase 0 workflow remains intact. No deployment is triggered.

## Phase 1 acceptance gates

- [x] Branch created from Phase 0 without touching main.
- [x] Changes isolated to reusable configuration/lifecycle modules, frontend date helper, tests, CI and documentation.
- [x] All backend tests pass on Phase 1 head SHA in GitHub Actions (**63 passed** at `96f256a2`).
- [x] Frontend unit tests and production build pass on Phase 1 head SHA in GitHub Actions (**3 passed**, production build successful).
- [x] Independent Antigravity local backend/frontend startup and test-account CRUD checks **reported** on upstream `96f256a2` (see QA report; browser UI remains untested).
- [ ] Reviewer approval of the Phase 1 PR.

## Preserved safeguards and outstanding risks

1. User data: no storage migration, destructive task policies or bulk account deletion changes. Export/deletion consent remains future work.
2. Concurrency: Phase 0 daily Firestore claim remains; task-write races, fencing and emulator stress tests still open.
3. LLM failure: no new mandatory model calls or service startup dependency on provider keys.
4. Notifications: no change to in-app event semantics; delivery guarantees and opt-in remain future work.
5. Tracking: keep the permanent tracker, phase audit, CI evidence and explicit unknowns.

## Running checks

From `backend/`: `python -m pip install -r requirements.txt`, then `python -m pytest -q`.  
From `frontend/`: `npm ci`, `npm test`, and `npm run build`.  
Use `CHRONOMIND_DISABLE_LEGACY_SCHEDULER=1` in test/local environments. Run frontend tests with `TZ=Asia/Kolkata` to explicitly cover midnight UTC/local date boundaries.

**Not verified here:** valid/expired/revoked Firebase tokens against a real test project, Firestore transactional races, full startup, real UI interaction and network-dependent LLM/notification delivery. Phase 0 PR cannot be approved based only on Phase 1 CI.

## CI evidence on initial implementation commit

- Commit: [`f1844556`](https://github.com/shanmukhdatta/Chrono-Mind-AI/commit/f1844556e039e7614100f1d7e107e5abfb8c8d1a).
- [Push run #38441356503](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38441356503) and [PR run #38441410275](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38441410275): both backend and frontend jobs **passed**.
- Backend pinned Python 3.11: **59 passed, 1 pytest-asyncio deprecation warning**; `compileall` passed.
- Frontend Node 20: **3 tests passed**, `npm ci` and `npm run build` passed. Vite reported bundle-size warning; dependency/runner deprecation notices were non-fatal.
- This is **initial-code-commit evidence**; a subsequent evidence/smoke-test commit must have its own final-head CI verified before approval.

## Antigravity QA finding and follow-up

The user-provided Windows QA report recorded 60/60 backend tests, 3/3 frontend tests, working HTTP startup, and 11/11 live test-Firebase operations after a **local, uncommitted** Firestore index workaround. See [Phase 1 QA intake](PHASE1_QA_REPORT.md). The GitHub branch now includes a reviewed index-free query implementation and tests; that new commit must pass CI and be rechecked against live Firebase. Browser automation, cross-worker concurrency, token expiry/revocation, and review sign-off remain outstanding.

## Second integration verification (2026-10-13)

The Antigravity runner reported a successful Windows retest **on the same GitHub SHA `96f256a2`** after preserving local uncommitted changes in a stash. It confirmed 63 backend tests, 3 frontend tests, Vite build, backend /health, authenticated Firebase CRUD, overlap conflict response, and indexed day/range queries without the earlier Firestore composite-index exception. The externally reported test count was 11/11, while ten HTTP request categories are itemized in the report. See [QA report](PHASE1_QA_REPORT.md).

Independent GitHub evidence on that SHA:
- [Push #38443760055](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38443760055): **success**.
- [PR #38443766957](https://github.com/shanmukhdatta/Chrono-Mind-AI/actions/runs/38443766957): **success**.

**Disposition:** Development foundation and CI evidence are ready for review. Browser automation failed to provision its Playwright driver; no interactive browser test is established. Phase 0 Firebase token edge cases and distributed concurrency remain pending. Reviewer sign-off and deliberate merge remain required. Do not advance to Phase 2 automatically.

## Deep verification evidence and repository hygiene

The third Antigravity report exercised the six requested areas using a scratch test harness, simulated Firebase errors and in-memory Firestore claim doubles. It **did not** run true multi-process Firestore/emulator concurrency tests or an interactive browser session. The existing task-create TOCTOU risk remains. Detailed test provenance: [PHASE1_QA_REPORT.md](PHASE1_QA_REPORT.md).

Phase 1 also removes 16 compiled Python artifacts accidentally tracked in nested packages, ignores future Python bytecode globally, and adds a CI check that rejects committed `.pyc` files. Two new reproducible pytest cases cover the expired/revoked error-handling branches with simulated exceptions. These are **unit tests** only.

Never commit test credentials. A test password was copied into the external report; rotate it before continued testing.

## Corrected browser acceptance checklist

The source-level review of `frontend/src/hooks/useAuth.js` confirmed Google OAuth popup login, **not** an email/password form. The earlier Antigravity guide described a UI that does not exist. Use the source-matched [manual browser acceptance checklist](PHASE1_BROWSER_QA.md), and do not mark UI verified until its checks are actually performed.
