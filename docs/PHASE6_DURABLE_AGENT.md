# Durable LangGraph planner — Phase 6 development slice

Authenticated APIs:
- POST /api/v2/agent/runs with `{"days":7}`
- GET /api/v2/agent/runs/{run_id}
- POST /api/v2/agent/runs/{run_id}/resume — only after the user has approved/rejected the corresponding proposal

The graph uses a tenant-scoped UUID thread_id (`verified_uid:run_id`) and PostgreSQL PostgresSaver checkpoints. It generates and validates a deterministic plan, persists a proposal idempotently (proposal id = run id), then **interrupts for human review**. Approval/rejection/undo remains entirely in the authenticated proposals API; no autonomous calendar writes are allowed. Resume reads the actual persisted decision, never a client-supplied approval string.

## Operator setup

Use a PostgreSQL server and the V2 Alembic schema. Back up the database and explicitly initialize the LangGraph checkpoint tables:

```powershell
$env:DATABASE_URL = 'postgresql+psycopg://USER:LOCAL_PASSWORD@localhost:5432/chronomind'
$env:LANGGRAPH_STRICT_MSGPACK = 'true'
cd backend
python -m alembic -c alembic.ini upgrade head
python -m scripts.init_langgraph_checkpoints
```

The API does not automatically create checkpoint tables. Production startup and test account must use matching configured credentials.

## Manual durable-recovery verification

1. Start a run with real Firebase authentication. Record run_id and proposal_id.
2. Confirm it is awaiting_review and the proposal exists in PostgreSQL.
3. Restart the API process and verify GET /agent/runs/{id} still reports awaiting_review.
4. Approve or reject that exact proposal through the authenticated plans API.
5. Resume the graph; it reports the stored decision without recreating a proposal.
6. Test a second user cannot see or resume the first user's run.
7. Verify no task/calendar data was modified before approval.

GitHub CI only verifies graph API and in-memory interrupt/resume; the restart test must be run against PostgreSQL before Phase 6 is accepted.
