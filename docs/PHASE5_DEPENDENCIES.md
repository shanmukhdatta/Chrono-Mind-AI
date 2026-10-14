# Task prerequisites — Phase 5 enhancement

Authenticated endpoints:
- GET /api/v2/tasks/{task_id}/dependencies
- POST /api/v2/tasks/{task_id}/dependencies with `{"depends_on_id":"owned-task-id"}`
- DELETE /api/v2/tasks/{task_id}/dependencies/{depends_on_id}

All edges are scoped to the verified Firebase user. Database locks serialize changes by owner. The graph rejects self-dependencies and transitive cycles, is duplicate-safe, and increments task versions to invalidate stale proposals.

The deterministic plan preview checks prerequisites: if any prerequisite is not **completed**, the dependent task is left unscheduled with an explicit reason. Existing scheduled blocks from before a dependency was added are NOT automatically rearranged or deleted; a later conflict/replan workflow must manage those changes.

This is intentionally conservative: the planner does not yet arrange incomplete prerequisites and their dependents within the same proposed schedule. Full dependency-aware joint optimization remains a documented extension. CI covers unit and tenant isolation; PostgreSQL concurrency acceptance remains pending.
