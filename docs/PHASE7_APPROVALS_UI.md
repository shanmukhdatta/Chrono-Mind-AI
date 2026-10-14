# Human review interface

Authenticated `/approvals` page: lists stored pending/approved/rejected/undone proposals, displays exact time block changes, unscheduled work and explicit confirmation prompts. Only pressing approve can execute a saved proposal. Reject performs no calendar mutation. Undo removes an approved plan's own blocks when they remain unchanged. Stale or conflicting proposals return a visible 409 error.

The `/planning` page can now create a durable proposal before taking the user to the review page. This is a real API workflow, not a simulated button. Demo users must sign in first. Test against live PostgreSQL and Firebase in Antigravity before merge.
