## Phase and scope
- Phase: <!-- e.g. Phase 2: PostgreSQL and authentication -->
- Base branch: <!-- main, after prior phase is merged -->
- Intended changes:
- Explicitly deferred work / known risks:

## Implementation review
- [ ] Scope matches the roadmap; no unrelated rewrite
- [ ] No real secrets, test account passwords, customer data, or generated build artifacts committed
- [ ] Database changes, if any, have a migration, dry-run and rollback plan
- [ ] No destructive production migration or deployment performed
- [ ] Security, concurrency, data ownership and error fallbacks considered

## Automated GitHub CI (must provide URLs)
- [ ] Backend tests and compilation green on exact PR head
- [ ] Frontend tests and build green on exact PR head
- [ ] Tracked-file hygiene check passed
- Workflow/run URL:
- Commit SHA:

## Antigravity local verification (performed separately)
- [ ] Fetched and tested exact PR head SHA
- [ ] Local services start and relevant integration paths work with test-only data
- [ ] No regression in previously working functionality
- [ ] Actual failures, warnings, and untested areas documented
- Antigravity evidence or report:

## Merge authorization
- [ ] Assistant reported code review and CI evidence, remaining risks and recommendation
- [ ] User explicitly reviewed and chose to merge the PR
- [ ] Next phase starts only from updated main after merge is verified

**Merges are performed by the user.** Never auto-merge or auto-deploy through this workflow. Green CI is not production sign-off.
