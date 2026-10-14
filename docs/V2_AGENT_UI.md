# LangGraph Agent Run screen

Protected `/agent-runs` page connects to the real V2 PostgreSQL-backed graph endpoint. It creates new agent runs, reveals the persisted approval proposal, shows status, links to authenticated Approval Center, and resumes only after the backend observes a stored approve/reject decision. The frontend never supplies an arbitrary 'approved' verdict.

Run IDs can be pasted after page reload. This is intentionally not a user-run history index: the API currently supports direct lookup, not listing. The system still needs real database restart recovery verification and full LangGraph bounded replanning from the README.
