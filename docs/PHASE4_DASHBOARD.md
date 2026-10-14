# V2 dashboard / transparent priority scoring

Authenticated GET /api/v2/dashboard returns counts of pending/completed/archived work, active goals, overdue tasks, today's scheduled effort, completion percentage, top-ten scored tasks, and seven-day completion counts.

Priority engine (deterministic, not trained): base=15, important +35, active goal +15, overdue +40, due within 24h +30, within 72h +20, within seven days +10, capped at 100. Scores and explanations are returned. These are product heuristics that will require evaluation and tuning, not claims of optimal scheduling. No advanced behavioral model or automatic date rescheduling is implied.

All queries are filtered by Firebase UID. Tests cover scoring monotonicity and tenant-separated dashboard. Real PostgreSQL/timezone regression still required.
