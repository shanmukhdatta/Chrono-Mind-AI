# ChronoMind AI V2 — Final README-to-Code Implementation Matrix

**Audit date:** 2026-10-22. **Branch:** `feat/chronomind-v2-complete-prototype` (from `v2/complete-core-product`).
**Evidence basis:** full local backend suite (137 passed, 2 skipped), frontend suite (36 passed), Vite production build, `python -m compileall`. Live PostgreSQL/Firebase/LLM/browser verification requires external services not available in this environment.

Statuses: **VERIFIED** (implemented + covered by passing local tests), **IMPLEMENTED-UNVERIFIED** (code complete, needs live-service/manual proof), **PARTIAL** (works with documented limits), **MISSING**, **BLOCKED** (external dependency).

Future extensions deliberately excluded from core scope (README §45–49): Kafka, Kubernetes, microservices, Redis, full RL, multi-agent orchestration, pgvector memory, external calendar import, OR-Tools solver, fine-tuned/on-device models, RAG assistant, A/B platform. Tracked in the roadmap section below, not counted as gaps.

## A. Authentication and user management

| README section | Feature | Source location | Status | Notes / evidence |
|---|---|---|---|---|
| §32, §33 | Firebase ID-token verification | `backend/middleware/auth.py` | VERIFIED | `tests/test_auth_security.py`; expired/invalid/revoked branches simulated |
| §7, §8 | PostgreSQL user profile + UID mapping | `backend/v2/models.py` (`User`), `backend/v2/db.py` | VERIFIED | Tenant `owner_uid` on every table; `get_or_create_user` |
| §32 | User-specific data isolation | every `backend/v2/*_api.py` query scoped by `owner_uid` | VERIFIED | Cross-user 404/empty assertions in dashboard, notifications, proposals, account tests |
| §51 | Account export | `backend/v2/account_data.py` `GET /api/v2/account/export` | VERIFIED | `test_v2_account_data.py`: private/no-store, owner-scoped |
| §51 | Account deletion (PostgreSQL + Firestore + checkpoints) | `backend/v2/account_data.py` `DELETE /api/v2/account` | IMPLEMENTED-UNVERIFIED | Purges all 18 V2 tables, legacy Firestore collections, and LangGraph checkpoint threads (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes` by `uid:%` thread prefix). SQLite tests cover the relational purge; live Firestore + checkpoint purge needs a real database |
| §32 | API error consistency | global handler in `backend/main.py`; 404/409/422 conventions | VERIFIED | Contract test asserts every V2 route is registered |

## B. Tasks and goals

| README section | Feature | Source location | Status | Notes / evidence |
|---|---|---|---|---|
| §8, §28 | Task CRUD + optimistic versioning | `backend/v2/api.py` | VERIFIED | `test_v2_api.py`, `test_task_service_regressions.py`; 409 on stale version |
| §28 | Archive/restore/complete/reopen + safe delete guards | `backend/v2/api.py` `PATCH`/`DELETE` | VERIFIED | Delete blocked when sessions/recurring occurrences exist; future blocks removed only on explicit complete/archive |
| §8 | Goals CRUD with status/weight influence on priority | `backend/v2/api.py`, `backend/v2/priority.py` (`goal_is_active` +15) | VERIFIED | `test_v2_api.py` |
| §8 | Task↔goal relations, SET NULL on goal delete | `models.Task.goal_id`, `_check_goal` | VERIFIED | Ownership checked before attach |
| §5, §8 | Dependencies + blocked explanations | `backend/v2/dependencies_api.py`, planner `blocked_reason` | VERIFIED | `test_v2_dependencies.py`; acyclic, owner-scoped, reason surfaces in preview `unscheduled` |
| §8, §35 | Daily/weekly/monthly recurrence, skips, idempotent materialization | `backend/v2/recurrence.py` | VERIFIED | `test_v2_recurrence.py`, `test_v2_replanning_and_account_deletion.py` (monthly, second materialize creates 0) |
| §17, §28 | Task splitting into ≤90-min sessions | `backend/v2/planner.py`, `splittable` flag | VERIFIED | `test_slot_planner.py`, `test_v2_splitting_policy.py` |
| §3, §17 | **Semantic subtask decomposition** | `backend/v2/decomposition.py`, `POST /tasks/{id}/decompose`, `GET /tasks/{id}/subtasks`, migration `0012_subtasks_monthly` | VERIFIED | LLM path with deterministic fallback; sequential dependency chain; `test_v2_decomposition.py` |
| §8 | Context tags on tasks (new) | `Task.context_tags`, migration `0013_focus_context`, `schemas.clean_context_tags` | VERIFIED | `test_v2_context_priority.py`: normalization, 422 on >5/blank tags, tenant isolation |
| §34 | Timezone-aware deadlines | `require_aware` in schemas, `ZoneInfo` in planning/recurrence | VERIFIED | Naive datetimes rejected with 422 |

## C. Calendar and scheduling

| README section | Feature | Source location | Status | Notes / evidence |
|---|---|---|---|---|
| §14 | Deterministic greedy scheduler (10-step README algorithm) | `backend/v2/planner.py` | VERIFIED | Pure functions; no LLM, no DB writes |
| §14 | Working hours, daily caps, min breaks | `Preference` → `PlanningPreferences` | VERIFIED | Enforced in preview and revalidated at approval |
| §14 | Fixed commitments occupy slots | `backend/v2/calendar_api.py`, `FixedEvent` in planner busy set | VERIFIED | `test_v2_calendar_api.py` |
| §14 | Free-slot calculation, deadline-aware, priority-sensitive placement | `planner._free_windows`, sort by `priority_score` | VERIFIED | `test_slot_planner.py` |
| §15 | Schedule validator (overlap, deadline, dependency, fixed-event, bounds) | `replanning._valid`, `agent_graph.validate_preview` | VERIFIED | `test_v2_evaluation.py`, `test_v2_agent_graph.py` |
| §16 | Bounded replanning (≤3 candidates, ≤3 graph attempts) | `replanning.choose_schedule` (`MAX_CANDIDATES=3`), graph retry `attempt < 2` | VERIFIED | Deterministic strategy list with reason codes |
| §16 | Candidate quality scoring | `replanning._quality` + `decision_trace.attempts` | VERIFIED | Exposed in preview and proposal `decision_trace` |
| §28 | Missed-session recovery in preview (past sessions never block fresh proposals) | `planning_api.get_preview` `end > generated` branch | VERIFIED | Regression test in `test_missed_task_policy.py` / audit fix #4 |
| — | **Proactive missed-task proposals on a managed schedule (new)** | `backend/scripts/propose_v2_replans.py` + `create_replan_proposal()` shared with `POST /api/v2/planning/replan` | IMPLEMENTED-UNVERIFIED | Candidate selection, cooldown, dry-run/apply gating tested (`test_v2_replan_worker.py`); live cron execution needs a deployed database |
| §14 | User-locked/protected blocks never silently moved | approval revalidation `verify_candidate`; move endpoint revalidates | VERIFIED | `test_v2_proposals.py`, `test_rescheduler_write_safety.py` |
| §51 | Transactional apply + undo | `proposals_api` approve/undo with owner/task locks | VERIFIED | Approve → blocks committed; undo restores; stale proposal → 409 |
| §51 | Unfinished work never silently deleted | delete guards; V1 destructive policy removed (Phase 0) | VERIFIED | `test_missed_task_policy.py` |
| — | Week/month calendar views (V2) | `frontend/src/pages/CalendarV2.jsx` + `lib/calendarV2.js` | VERIFIED | Day/week/month windows; `calendarV2.test.js` |

## D. Intelligent priority engine (README §13)

| Signal | Source location | Status | Notes |
|---|---|---|---|
| Manual importance | `priority.score_task` +35 | VERIFIED | Reason "Marked important" |
| Deadline urgency | +40/+30/+20/+10 tiers | VERIFIED | `test_v2_dashboard.py` monotonicity |
| Active goal relevance | +15 | VERIFIED | |
| **Postponement pressure** | +5/event capped +15, counted from past schedule sessions on pending tasks | VERIFIED (new) | `planning_api` + `dashboard_api`; reason "Postponed N time(s)" |
| Task dependencies | +5/dependent capped +15, −25 if blocked | VERIFIED | |
| **Current user context** | `Preference.focus_context` × `Task.context_tags` +15 | VERIFIED (new) | Deterministic token match `priority.context_matches`; dashboard exposes `focus_context` and per-task tags |
| **Effort + flexibility** | quick win ≤15 min +5; unsplittable +5 | VERIFIED (new) | |
| Behavioral fit | opt-in preferred focus hour +10 | VERIFIED | Consent-gated (`BehaviorConsent`) |
| Explainability | every score ships `priority_reasons`; scoring weights published in dashboard payload | VERIFIED | `test_v2_context_priority.py`, DashboardV2 renders reasons |

No hardcoded category ranking: scoring inputs are user data only (README §3 "The system never assumes one category is always more important").

## E. Notifications, focus, and background jobs

| README section | Feature | Source location | Status | Notes |
|---|---|---|---|---|
| §8, §31 | Persistent in-app notifications + dedupe | `backend/v2/notifications_api.py` (`uq_v2_notification_owner_key`) | VERIFIED | `test_v2_notifications.py`: idempotent regeneration, owner-scoped read |
| §31 | Deadline/upcoming/missed reminder generation | `create_daily_notifications` (overdue + due_today, local-day keys) | VERIFIED | |
| §31 | **Managed cron execution (new)** | `render.yaml`: `chronomind-v2-notifications` (06:00), `chronomind-v2-recurrence` (hourly), `chronomind-v2-replans` (05:00) | IMPLEMENTED-UNVERIFIED | Jobs are flag-gated (`CHRONOMIND_*_JOB_ENABLED=1`); dry-run default; deployment wiring needs a live Render project |
| §31 | Operator scripts for local/scheduled runs | `scripts/generate_v2_notifications.py`, `scripts/expand_v2_recurrence.py`, `scripts/propose_v2_replans.py`, `scripts/init_langgraph_checkpoints.py` | VERIFIED | All dry-run by default, bulk writes require explicit env flag |
| §9, §24 | Focus timer persistence + consent-aware behavior events | `backend/v2/focus_api.py` | VERIFIED | `test_v2_focus_api.py`; consent endpoint, no events without consent |
| §24 | Behavior → planner feedback | `planning_api` preferred-hour inference (`personalization.preferred_work_hour`) | VERIFIED | Reported in preview `personalization` block |
| §31 | V1 APScheduler no longer required for V2 | `CHRONOMIND_DISABLE_LEGACY_SCHEDULER=1` in `render.yaml` | VERIFIED | Legacy scheduler remains available but disabled in deploy config |

## F. LangGraph agentic engine (README §9–12, §18)

| README section | Feature | Source location | Status | Notes |
|---|---|---|---|---|
| §10–12 | Single planning workflow: intake → generate → validate → (bounded retry) → store → await_human → complete | `backend/v2/agent_graph.py` | VERIFIED | `test_v2_agent_graph.py` covers valid, retry, exhausted paths |
| §9 | Durable Postgres checkpoints | `PostgresSaver` in `agent_api.compiled_graph`; `LANGGRAPH_STRICT_MSGPACK` | IMPLEMENTED-UNVERIFIED | Graph logic tested with in-memory checkpointer; live restart recovery needs real PostgreSQL |
| §18 | Human-in-the-loop: graph pauses at `interrupt`, verdict read only from owner's approval record | `agent_api.begin_run`/`resume_run` | VERIFIED | Caller cannot supply verdict; 409 until proposal approved/rejected |
| §18 | High-impact change approval | proposals `pending → approved/rejected/undone`, 1-hour expiry, preference/version revalidation | VERIFIED | `test_v2_proposals.py` |
| §25 | Decision logging | `PlanningDecisionLog` (proposed/replanned/approved/undone) | VERIFIED | `test_v2_replanning_and_account_deletion.py` |
| §12 | Triggers: user action + scheduled job | `POST /api/v2/agent/runs`, `POST /api/v2/planning/replan`, cron worker (new) | VERIFIED | |
| §11 | Transactional execution | approve path: owner lock → task version lock → conflict check → insert blocks → commit | VERIFIED | `test_rescheduler_write_safety.py` |

## G. Assistant, model routing, voice (README §19–23)

| README section | Feature | Source location | Status | Notes |
|---|---|---|---|---|
| §19–20 | Structured outputs, schema-validated, no regex parsing | `backend/v2/assistant.py` Pydantic `AssistantDecision` | VERIFIED | `test_v2_assistant.py` |
| §19 | Validated drafts: task/goal create, task change (update/complete/archive/delete), goal change, decomposition, schedule query | `assistant.py` draft kinds + frontend confirm flow in `AssistantV2.jsx` | VERIFIED | Nothing persists without explicit user confirmation |
| §21 | Model router: no-LLM / fast / reasoning tiers | `backend/v2/llm_router.py`, `model_router.py` | VERIFIED | `test_v2_model_router.py`; Groq tier routing commit `ba3d76a` |
| §22 | Cost controls + token/latency metrics | `AssistantMetric` table, `GET /api/v2/assistant/metrics` | VERIFIED | `test_v2_assistant.py` |
| §23 | Voice input with typed fallback | `frontend/src/components/VoiceButton.jsx` (browser STT), chat text input always available | IMPLEMENTED-UNVERIFIED | Real microphone/browser QA is external |
| §19 | Daily briefing | `GET /api/v2/assistant/briefing` | VERIFIED | |

## H. Personalization, explainability, observability, evaluation (README §24–27)

| README section | Feature | Source location | Status | Notes |
|---|---|---|---|---|
| §24 | Opt-in behavior profile | `BehaviorConsent` + `PUT /api/v2/focus/consent` | VERIFIED | Default off |
| §25 | Priority explanations | `priority_reasons` on dashboard and tasks | VERIFIED | |
| §25 | Before/after audit history | `PlanningDecisionLog.before_blocks/after_blocks` | VERIFIED | |
| §26 | Per-user token/latency/cost metrics API | `assistant_metrics` | VERIFIED | Operator cost rates via env |
| §27 | Evaluation suite | `backend/v2/evaluation.py`, `evals/scenarios.jsonl` (120×2), `backend/evals/` | VERIFIED | `test_v2_evaluation.py`, `test_v2_evaluations.py` |
| §27 | Agent regression tests | `tests/test_v2_agent_graph.py`, `test_langgraph_upgrade.py` | VERIFIED | |

## I. Frontend (README §29–30)

| README section | Feature | Source location | Status | Notes |
|---|---|---|---|---|
| §29 | V2 screens on one design system | `layouts/AppShell.jsx`, `components/ui/*`, `styles/globals.css` (Tailwind tokens: peach/dark/peach-dark) | VERIFIED | Dashboard, Tasks, Calendar, Goals, Planning, Approvals, Assistant, Focus, Recurrence, Notifications, Profile, Agent Runs share shell/nav |
| §30 | Authenticated API client, token refresh | `lib/api.js` | VERIFIED | One refresh retry, 401 → login |
| — | **Demo mode never fabricates V2 success (new)** | `lib/api.js` catch-all now rejects unknown endpoints instead of resolving fake success | VERIFIED | Legacy V1 demo simulation retained only for exact V1 task routes; V2 pages show explicit sign-in notices |
| §8, §13 | Context tags + focus context UI (new) | `TasksV2.jsx` tag input, `PlanningSettings.jsx` focus context field | VERIFIED | `tasksV2.test.js`, `planningPreferences.test.js` |
| §29 | Responsive layout | Tailwind responsive classes across pages | PARTIAL | Works at tested widths; full screen-size QA is external |
| §6 | TypeScript migration | all `.jsx` | PARTIAL | Deliberately deferred: JS/JSX prototype with passing tests; migration tracked as future work, not a functional gap |
| — | Accessibility | labels/aria on key controls (`aria-label` on edits, refresh, filters) | PARTIAL | Semantics present but no automated a11y audit in this environment |

## J. Security and operations (README §32–33, §38–41)

| README section | Feature | Status | Notes |
|---|---|---|---|
| §33 | Agent never gets unrestricted DB access; all writes via validated tools/endpoints | VERIFIED | Graph cannot approve its own proposals |
| §33 | Never trust client-sent owner IDs | VERIFIED | `owner_uid` always from verified token |
| §38 | Graceful LLM failure: deterministic scheduler survives provider outage | VERIFIED | Decomposition/assistant fallback paths tested |
| §40 | Environment configuration | VERIFIED | `backend/.env.example`, `render.yaml` (web + 3 cron jobs) |
| §39 | Deploy configs | PARTIAL | Render/Vercel configs exist for V1; V2 web + cron defined in `render.yaml` but **not deployed/verified** |
| §36 | Known V1 issues (future-slot collision, look-ahead gap, date-only conflict, regex actions, night reliability, silent deletion, sparse tests) | VERIFIED in V2 paths | V2 planner/validator/scheduler address each; V1 legacy endpoints retained but not used by V2 screens |

## K. Testing evidence (this session)

| Command | Result |
|---|---|
| `cd backend && ./.venv/Scripts/python.exe -m pytest -q` | **137 passed, 2 skipped** |
| `cd backend && ./.venv/Scripts/python.exe -m compileall -q .` | clean |
| `cd frontend && npm test` | **36 passed** (10 files) |
| `cd frontend && npm run build` | Vite production build succeeds |
| Live PostgreSQL Alembic migration + checkpoint recovery (`test_v2_live_postgres.py`) | SKIPPED — needs disposable PostgreSQL (`CHRONOMIND_TEST_POSTGRES_*`); no Docker/psql in this environment |
| Live Firebase auth flow, real Groq LLM calls, browser/microphone QA | NOT RUN — external credentials/devices required |

New tests added this session: `test_v2_context_priority.py` (2), `test_v2_replan_worker.py` (6), plus extended `planningPreferences.test.js` (+2) and `tasksV2.test.js` (+1).

## L. Remaining external blockers

1. **Disposable PostgreSQL** — run `test_v2_live_postgres.py` (migration head `0013_focus_context`, approval persistence, owner isolation) against a real database.
2. **Firebase test project** — live sign-in, expired/revoked tokens, cross-device sessions.
3. **Deployed Render project** — verify the three new cron jobs actually fire and the flag-gated writes run on schedule.
4. **Groq API key** — live assistant chat, decomposition LLM path, model-router latency/cost metrics (fallback paths are tested).
5. **Real browser QA** — sign-in → task CRUD → preview → approve → undo walkthrough, voice input, responsive/a11y checks.
6. **TypeScript migration** — quality/robustness goal, deferred by design; not required for functional completeness.

## Future roadmap (README §45–49 — intentionally not in core V2)

Redis caching/queues, Kafka event streaming, microservices split, Kubernetes, multi-agent orchestration, full reinforcement learning, contextual bandits, learning-to-rank, fine-tuned/local models, pgvector semantic memory, developer RAG assistant, external calendar sync, multimodal timetable import, notification intelligence (push/email providers), experimentation platform, data warehouse, OR-Tools optimization upgrade.
