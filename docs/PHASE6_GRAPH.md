# LangGraph V2 planning workflow

Six-node graph: intake → generate preview → validate intervals → idempotent persist proposal → **human interrupt** → complete. The graph does not apply calendar changes itself; the user must approve or reject the persisted proposal using the separate authenticated API. A PostgreSQL checkpointer is required for production so graph state survives process restarts.

A dedicated graph regression uses the in-memory checkpointer to prove checkpointed interruption and resume without repeating a persistence operation. This is a test double only. Real PostgreSQL checkpoint initialization, restart recovery, thread isolation and resume correctness require a live integration run.

Backend workflow orchestration and an API will be implemented on top of this graph. No LLM is required for the deterministic planning flow; intent extraction comes later.
