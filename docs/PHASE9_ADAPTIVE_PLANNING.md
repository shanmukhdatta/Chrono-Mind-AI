# Opt-in behavioral personalization applied to schedule proposals

After the user enables behavioral insights and records at least five completed focus sessions, V2 planning reads only coarse hour-of-day and duration signals and derives a preferred work-hour using deterministic duration-weighted counts.

The schedule builder then prefers valid candidate work slots near that hour **as a soft preference**. Hard constraints (busy intervals, deadlines, breaks and daily effort caps) remain mandatory. No full reinforcement learning or fine-tuned model is claimed. The API returns `personalization.applied` and `personalization.preferred_hour` so users can understand the reason.

Without consent or sufficient events, the planner uses the original earliest-slot strategy. Revoking consent deletes behavior events through the Focus API and planning immediately returns to its nonpersonalized behavior. Generated plans remain proposals; all calendar commits still require user approval and conflict revalidation.

Before production: test representative schedules, deadline trade-offs, daylight-saving transitions, user preference overrides and real PostgreSQL consent isolation.
