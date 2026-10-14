# LangGraph upgrade and Postgres checkpoint compatibility

This PR updates the older LangGraph 0.1.x dependency to LangGraph 1.2.x, upgrades compatible LangChain Core/Pydantic pins, and installs the PostgreSQL checkpointer package. It does not migrate or create checkpoint tables by itself.

The server must not call `PostgresSaver.setup()` on arbitrary startup. Initialize checkpoint schemas using an explicit operator command (with a database backup), and set `LANGGRAPH_STRICT_MSGPACK=true` in the deployment configuration. The checkpointer connection must use a PostgreSQL URL, and production graphs must compile with a checkpointer and a tenant-scoped thread_id.

CI verifies compilation of a small graph, checkpoint replay via in-memory saver, and availability of the PostgresSaver implementation. These tests do NOT prove live PostgreSQL checkpoint recovery. That requires a local PostgreSQL restart test in Antigravity before Phase 6 sign-off.

Do not merge this dependency migration unless existing legacy rescheduler regressions and the entire API/frontend test suite remain green.
