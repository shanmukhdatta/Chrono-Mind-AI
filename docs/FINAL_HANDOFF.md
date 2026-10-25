# ChronoMind AI V2 — Final handoff and truthful project status

**Last source-review checkpoint:** 2026-10-25. `main` at audit start: `d45476ed2916631cfe971381c8587b676699b3f2`. Finalization work is isolated in PR branch `finalize/v2-minimal-ui-and-correctness` until reviewed and merged by the owner.

## What exists

- V2 React interface with Dashboard, Tasks, Goals, Calendar, Planning, Approvals, Assistant, Focus, Recurrence, Notifications, Agent Runs, Preferences, and Profile.
- SQLAlchemy PostgreSQL schema and Alembic migrations through `0013_focus_context`; Firebase UID authorization and owner-scoped queries.
- Deterministic priority scorer, availability-based greedy scheduler, bounded replanning and approval/undo logic.
- LangGraph human-interrupted workflow with PostgreSQL checkpointer; Groq structured draft-and-confirm assistant with deterministic fallback; opt-in focus-hour heuristic.
- Operator-managed scripts for notifications, recurrence and replanning; GitHub Actions backend/frontend checks and disposable PostgreSQL migration tests.
- Read-only, visibly marked public demo at `/demo` and protected, localhost-only test fixture seeding.

## Corrections in the finalization branch

- Simplified landing page, sidebar and typography; removed decorative motion, retained keyboard focus indicators; static UI demo distinguishes mock sample data from user records.
- Subtask ancestors are owner-verified, cycles blocked, and parents with child tasks excluded from the schedule/priorities; parents with children cannot be silently deleted.
- Decomposition is not repeated on an already-decomposed parent and cannot be applied on already-booked work. Confirmed assistant subtask drafts are applied as-is with duration validation.
- At proposal approval time, revalidate that planned tasks have not become containers and prerequisites remain fulfilled.
- Assistant instruction/schema consistency for goal changes and bounded decomposition, with server-side ownership validation.
- Account data purge acknowledges Firebase Auth identity is NOT deleted and reports incomplete external-store cleanup instead of declaring complete erasure.
- Environment templates and local only sample fixture script; canonical guide for resuming and technical feature map.

## Explicit status, not marketing

**Substantial V2 code prototype: yes. Production readiness: not verified.** The README remains the *design specification*, including optional features deferred from V2 core.

At audit time `main` had successful GitHub Actions runs, including V2 backend/frontend and disposable PostgreSQL integration. Those success results predate this branch. **Do not state that the finalization branch passes until its own CI run is completed.**

## Required final acceptance (not proved by source alone)

1. Merge only after branch CI turns green; if red, address actual test output.
2. Local Firebase + real PostgreSQL and LangGraph restart/resume test using the setup guide.
3. Live Groq draft creation and decomposition, including provider outage fallback.
4. Exercise all V2 workflows in desktop + narrow mobile browsers and test accessible keyboard navigation.
5. Confirm cron jobs fire in the deployed environment and never auto-apply dangerous proposals.
6. Test full account-data cleanup across Postgres, Firestore, LangGraph tables and separately manage Firebase Authentication identity.
7. If migrating legacy Firestore user records, secure backup, dry run, reconcile and authorize cutover before any writes.

## Resume protocol

Check the current branch/PR status first. Read `docs/SETUP_V2.md`, `docs/FEATURE_MAP.md` and recent CI. Use a disposable DB, not a production account. Do not claim deployment without screenshots/logs from actual endpoints. Keep optional OR-Tools, RL, multi-agent, RAG, external calendars, push notifications and distributed infrastructure on the future roadmap rather than making them fake implemented features.

**Human merge gate:** this branch should remain separate from `main` until reviewed. Do not auto-merge other dependency PRs.
