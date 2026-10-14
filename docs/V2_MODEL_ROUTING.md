# V2 basic model routing and usage counters

Simple bounded 'list/count pending tasks' queries use authenticated database context without an LLM call. The remaining structured interpreter requests go to either the fast Groq tier or the reasoning tier according to deterministic request complexity indicators. Fast and reasoning models are configurable via `CHRONOMIND_LLM_FAST_MODEL` and `CHRONOMIND_LLM_REASONING_MODEL` but must remain within the allowlist. Legacy `CHRONOMIND_LLM_MODEL` remains a fallback. Logs contain model, latency, prompt token count and completion token count when Groq supplies it. The API exposes round-trip latency_ms.

**Limits:** The deterministic task list is capped to the 40-task context (and names only eight), not a complete query/search interface; the complex routing rule is heuristic, not a learned classifier. There is not yet a cost dashboard, multi-provider fallback or full tool-call suite; the README audit marks those as partial.
