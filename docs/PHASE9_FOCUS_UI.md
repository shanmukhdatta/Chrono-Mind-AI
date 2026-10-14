# V2 Focus Studio

Protected route `/focus-v2` integrates the real PostgreSQL focus session and consent APIs. Start a session, monitor its server-based countdown, finish or abandon it, reload after a browser restart, review recorded focus time, and explicitly opt into coarse personalized insights.

**Privacy:** Recording behavioral event statistics defaults off. Disabling consent deletes behavior-event rows. Focus-session history is retained unless the user explicitly deletes account data, which is a separate data-control feature to be implemented.

**Verification:** V2 database and Firebase sign-in are needed for live UI tests. Browser countdown is not the authority on elapsed time. Active sessions may exceed planned duration visually; the server caps the logged completion time. Behavior-based scheduling itself is not yet enabled.
