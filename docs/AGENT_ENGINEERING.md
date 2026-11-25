# ChronoMind agent engineering plan and implementation

The existing V2 assistant drafts changes, the planning graph checkpoints and pauses for approval, and the scheduler calculates feasible time blocks. Workspace research adds a separate question-answering workflow at POST /api/v2/assistant/investigate and a control in the assistant screen. Voice transcription feeds the same input.

| Features | Agent responsibility | Application responsibility |
|---|---|---|
| Tasks, goals, subtasks, dependencies | Work specialist retrieves matching records and prerequisite links | Existing draft validation, version checking and confirmed edits |
| Fixed events, scheduled blocks, recurrence | Calendar specialist reads upcoming evidence and series | Conflict checks, recurrence expansion, calendar edits |
| Preview, replan, preferences, approvals | Planning specialist invokes the existing seven-day preview and retrieves preference and proposal evidence | Search, validation, approval, rejection, undo and durable agent runs |
| Dashboard and priorities | Progress specialist explains computed counts and score reasons | Database aggregations and priority scoring |
| Focus and personalization | Focus specialist checks consent before fetching insights | Timer, consent removal and preferred-hour estimation |
| Notifications | Inbox specialist reads recent in-app messages | Notification generation and delivery state |
| Voice, profile, account export/deletion, legacy UI | Voice can submit a research question | Identity, destructive actions, legacy compatibility and export stay in their existing interfaces |

## Revised design

1. Supervisor selects one or two domain specialists using a validated JSON contract.
2. Each selected specialist receives only its authenticated tool results. Task, goal and calendar title lookup ranks literal query terms in SQL. Other sources use filters, summaries or a chronological sample. This is structured retrieval-augmented generation.
3. Each model handoff receives the user question, one role instruction, a JSON schema and at most 7,500 serialized characters of evidence. The harness allows up to three sequential provider calls with an individual timeout. The model has no database credentials or write tool.
4. Validate source identifiers against the delivered packet. Display the combined specialist answers and original source fields in the UI. Existing chat handles confirmed drafts. Agent research errors are visible and do not mutate schedules.
5. Run pytest for deterministic integration and contract checks. With a Groq key configured run `python -m evals.workspace_agents` from backend for a six-case live smoke eval. It reports per-domain routing, citation and answer-key success as a combined pass, plus latency.

## Design review and remaining work

A separate model per CRUD button would duplicate authorization and increase latency. Group agents by evidence domain and reuse application services. The current harness implements read-only investigation and existing confirmed drafts as two user-selectable modes. Record-key validation proves provenance, not factual entailment. Two independently written findings can disagree. Next evaluate cross-domain synthesis with human-labelled conflicting records, paraphrases, absent facts, and date-range queries. Track retrieval recall, citation entailment, factual accuracy, abstention, token cost and latency against single-call chat before making research the default. Add a synthesis call only if it improves that comparison. Persist redacted run-level measurements and add multi-turn retrieval if user trials justify it. Live provider quality and authenticated browser behavior require separate verification.
