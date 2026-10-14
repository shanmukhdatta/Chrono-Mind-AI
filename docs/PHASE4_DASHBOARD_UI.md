# V2 home dashboard

Protected `/dashboard-v2` is powered by the PostgreSQL `GET /api/v2/dashboard` endpoint. No fake counts or LLM-generated metrics. It offers pending/completed/overdue counts, active goals, scheduled work today, completion percentage, explainable ranked tasks, seven-day completions, and navigation to active V2 features.

Legacy `/dashboard` remains available until a verified Firestore-to-PostgreSQL migration. Verify with user accounts, live PostgreSQL and mobile browser before cutover.
