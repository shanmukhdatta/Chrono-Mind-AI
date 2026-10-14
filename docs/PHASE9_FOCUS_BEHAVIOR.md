# V2 focus sessions and opt-in behavioral summaries

Endpoints:
- POST /api/v2/focus/sessions, body `{"task_id":null,"planned_minutes":25}`
- POST /api/v2/focus/sessions/{id}/finish, body `{"outcome":"completed"}` or `{"outcome":"abandoned"}`
- GET /api/v2/focus/sessions; GET /api/v2/focus/insights
- GET /api/v2/focus/consent; PUT /api/v2/focus/consent with `{"enabled":true|false}`

Focus sessions are persistent, user-owned PostgreSQL records. A server-generated started_at and ended_at determine recorded duration, capped at the planned seconds. Browser reload/reconnect does not reset the server timestamp. The server prevents more than one active session per user.

Behavioral event recording **defaults off** and is opt-in. Events keep only coarse hour-of-day and duration, not raw voice/chat content. Opting out deletes behavior-event history, not focus-session records. The API returns no preferred-hour suggestion until at least five opted-in completed sessions exist. The preference is an interpretable heuristic, not trained ML. The task planner does not yet automatically apply behavioral preferences.

Tests use isolated SQLite; PostgreSQL concurrency, timer/browser restarts and long-lived sessions require Antigravity verification.
