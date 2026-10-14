# Deterministic schedule preview slice

Route: `GET /api/v2/planning/preview?days=7` with a valid Firebase ID token and configured PostgreSQL.

This **does not write schedules**. It reads pending tasks, existing scheduled sessions, fixed events and saved preferences, then returns possible new sessions and reasons for unscheduled work. No LLM calls are required; scheduling still works without an AI provider. Work is split into sessions of at most 90 minutes and considered only inside the user's configured work window. Previews are subject to user timezone, daily effort cap, busy intervals and task deadlines.

Pure engine tests verify overlap exclusion, limit enforcement, stable priorities and deadline-aware partial results. End-to-end live Postgres and clock boundary testing are still required. Before approval/commit support ships, all preview results must be labeled proposals, never persisted events.

**Future phase:** durable proposals, human approval, collision-protected database transaction, undo, LangGraph checkpoints, richer dependencies/recurrence, and front-end review.
