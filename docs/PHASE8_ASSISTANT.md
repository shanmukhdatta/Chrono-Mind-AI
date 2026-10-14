# Structured V2 assistant — safe action drafts

Authenticated endpoints:
- `POST /api/v2/assistant/chat` — answer or structured **draft** task/goal. No database writes occur here.
- `GET /api/v2/assistant/briefing` — deterministic pending/overdue/deadline summary even when no LLM is available.

Provider is Groq via server-side `GROQ_API_KEY`; choose `CHRONOMIND_LLM_MODEL` from `llama-3.1-8b-instant` (default) or `llama-3.3-70b-versatile`. JSON-object mode is used with Pydantic validation (not claimed to be strict-schema mode for Llama). The provider is untrusted; unsupported or invalid structured outputs become deterministic fallback rather than fabricated actions. A draft's `goal_id` must belong to the current user. Requests cap user input to 2,000 characters and context to at most 40 pending tasks/20 active goals.

**Critical confirmation boundary:** Even if the model says create a task/goal, response contains only a draft. The user must explicitly confirm it via the V2 UI, which invokes authenticated PostgreSQL task/goal CRUD APIs. Never say the action succeeded until backend returns success.

The task/calendar CRUD remains available without Groq; no custom LLM training is needed. Provider API tests use stubs; actual voice and Groq integration need device/service tests in Antigravity.
