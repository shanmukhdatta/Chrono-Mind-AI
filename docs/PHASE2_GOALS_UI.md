# Goals page — separate frontend PR

Route: `/goals`, protected by the existing Firebase frontend session.

- Uses authenticated API client and the new PostgreSQL `/api/v2/goals` and `/api/v2/tasks` routes.
- Supports create, list, select, edit, change status, delete, add task and mark task completed.
- Displays real server errors and never simulates database writes for demo users.
- Deleting a goal preserves linked tasks; the backend owns tenant isolation.
- Browser testing needs a real user session and a configured PostgreSQL database.
- This PR is stacked on the PostgreSQL domain PR; do not merge before the base PR is accepted.
