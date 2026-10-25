# ChronoMind AI V2 — Feature map and technical entry points

This is a **source-code navigation guide**, not a certification that live cloud services are configured. V2 data is in PostgreSQL; Firebase Auth identifies users. React talks to FastAPI. SQLAlchemy/Alembic manage relational data; LangGraph coordinates human-reviewed planning.

| User capability | Frontend route | Backend module | Data / mechanism |
|---|---|---|---|
| Tasks, edit, archive, complete | `/tasks-v2` | `v2/api.py` | `v2_tasks`, versioned writes |
| Goals and linked tasks | `/goals` | `v2/api.py` | `v2_goals`, foreign key |
| Priorities and reasons | `/dashboard-v2` | `v2/priority.py` | Weighted deterministic score, not a trained ML model |
| Calendar and fixed commitments | `/calendar-v2` | `v2/calendar_api.py` | `v2_fixed_events`, `v2_schedule_blocks` |
| Planning preview | `/planning` | `v2/planner.py`, `v2/planning_api.py` | Greedy bounded allocation; no write before approval |
| Adaptive replanning | `/planning` | `v2/replanning.py`, `scripts/propose_v2_replans.py` | Compare alternative schedules; proposed plans |
| Task decomposition and dependencies | `/tasks-v2` | `v2/decomposition.py`, `v2/dependencies_api.py` | LLM or deterministic steps; directed prerequisites |
| Approve, reject, move, undo | `/approvals` | `v2/proposals_api.py` | Transactional proposal state and decision history |
| Conversational assistant | `/assistant-v2` | `v2/assistant.py`, `v2/llm_router.py` | Groq JSON drafts with Pydantic validation and confirmation |
| Voice input | `/assistant-v2` | Browser SpeechRecognition | Browser-supported speech-to-text only |
| Focus and basic personalization | `/focus-v2` | `v2/focus_api.py`, `v2/personalization.py` | Consent-gated, deterministic preferred-hour heuristic |
| Recurring tasks | `/recurrence-v2` | `v2/recurrence.py` | Daily, weekly, simple monthly expansion; idempotency |
| In-app notifications | `/notifications-v2` | `v2/notifications_api.py` | Local-day due/overdue alerts; no email/push |
| Productivity dashboard | `/dashboard-v2` | `v2/dashboard_api.py` | Query-time metrics derived from real records |
| Preferences | `/preferences` | `v2/api.py` | Work windows, timezone, limits, context |
| Agent runs and audit trail | `/agent-runs` | `v2/agent_graph.py`, `v2/agent_api.py` | LangGraph PostgreSQL checkpointing, interruption |
| Authentication and data controls | `/profile` | `middleware/auth.py`, `v2/account_data.py` | Firebase UID scoping, SQL export, best-effort cross-store purge |

## Important product promises and limits

- Task rows and scheduled time blocks are distinct. Approving a proposal inserts blocks; previews never do.
- Plans are **human approved**. The current code does not silently apply large scheduling changes.
- Decomposed parent tasks are containers and are excluded from actionable scheduling. Direct child links are owner checked and cycle checked.
- Groq is optional for the deterministic planner; a provider outage must not prevent task CRUD.
- The assistant is a draft-and-confirm interface, **not** an agent with arbitrary database access.
- A V2 SQL data purge is **not** identical to complete account erasure. Firebase Auth deletion and external-store cleanup require explicit verification.
- `/demo` is static and read-only. `scripts/seed_v2_demo.py` seeds only a disposable localhost DB with explicit operator opt-in.
- Live Firebase, Groq, cross-store deletion, browser voice and actual production scheduling are acceptance gates, not certified by source-only review.

See [SETUP_V2.md](SETUP_V2.md) and [FINAL_HANDOFF.md](FINAL_HANDOFF.md).
