# ChronoMind AI 🧠⏰

**AI-Powered Day Planner for College Students**  
Built with FastAPI · LangGraph · Groq · React · Firebase

## Live Deployments 🚀
- **Frontend App:** [https://chronomind-ai.vercel.app](https://chrono-mind-ai.vercel.app/) 
- **Backend API Docs:** [https://chronomind-backend.onrender.com/docs](https://chronomind-backend.onrender.com/docs) 

---

> **An adaptive personal planning agent that prioritizes, schedules, replans, and explains a user's work based on goals, deadlines, availability, and learned behavior — while keeping the user in control.**

ChronoMind V2 is the redesign of the original ChronoMind AI day planner into a production-style **agentic AI planning system**.

The goal is not to build a chatbot that simply creates tasks. The goal is to build a reliable AI planning agent that can understand a user's changing priorities, produce feasible schedules, adapt when plans fail, learn preferences from behavior, and ask for approval before making high-impact changes.

---

# 1. Why ChronoMind V2?

The original ChronoMind already provides:

- Manual task creation
- Calendar views
- Google/Firebase authentication
- Voice input
- AI scheduling assistant
- Task completion tracking
- Recurring tasks
- Notifications
- Focus timer
- A LangGraph nightly rescheduling workflow

V2 keeps the useful product foundation but redesigns the AI architecture.

The original rescheduler is mostly a deterministic workflow:

```text
fetch incomplete tasks
        ↓
fetch tomorrow
        ↓
compute free slots
        ↓
assign slots
        ↓
write changes
        ↓
delete low-priority unfinished tasks
        ↓
notify user
```

ChronoMind V2 turns this into a true planning system:

```text
understand situation
        ↓
load user goals + behavior
        ↓
calculate task priorities
        ↓
build candidate plan
        ↓
split tasks if necessary
        ↓
validate constraints
        ↓
evaluate plan
        ↓
replan if necessary
        ↓
ask user when impact is high
        ↓
execute
        ↓
observe outcome
        ↓
learn for future planning
```

---

# 2. Product Vision

ChronoMind should continuously answer:

> **Given what the user wants to achieve, what they already committed to, what remains unfinished, how much time is available, and how they usually work, what should their schedule become now?**

The AI should assist the user, not take control away from them.

Major changes remain user-controlled.

---

# 3. Core V2 Capabilities

## Intelligent Prioritization

Tasks receive dynamic priority scores using:

- Explicit user priority
- Deadline urgency
- Goal relevance
- Current life/academic context
- Number of postponements
- Task dependencies
- Flexibility
- User behavior
- Estimated effort

Example:

```text
Current context: Placement Season

DSA Practice              → very high
Aptitude Practice         → high
Interview Preparation     → high
Semester Work             → medium/high
Optional Movie            → low
```

The system never assumes that one category is always more important. The user defines goals and ChronoMind adapts around them.

## Adaptive Rescheduling

Unfinished tasks are not blindly moved to tomorrow.

ChronoMind considers:

```text
deadline
priority
tomorrow's workload
available slots
previous postponements
preferred focus time
task duration
task flexibility
dependencies
```

It may place the task tomorrow, later in the week, split it, or ask the user.

## Task Splitting

Large tasks can be decomposed when no single block is available.

Example:

```text
Complete ML presentation — 3 hours

Available:
09:00–10:00
15:00–16:00
20:00–21:00

Possible plan:
09:00–10:00 → Research
15:00–16:00 → Build slides
20:00–21:00 → Review and practice
```

Simple splitting is rule-based. Semantic decomposition can use an LLM only when necessary.

## Replanning

ChronoMind can detect that a candidate plan is invalid or poor and build another plan.

```text
candidate plan
     ↓
validator
     ↓
invalid
     ↓
replan
     ↓
new candidate
     ↓
validator
```

Replanning is capped to avoid infinite loops.

## Human in the Loop

Small safe changes can be applied automatically.

High-impact changes require approval.

Examples requiring approval:

- Moving several tasks
- Moving deadline-critical work
- Splitting an important task across days
- Replacing a user-protected time block
- Changing a large part of tomorrow's schedule

User options:

```text
Accept Plan
Modify
Keep Current Schedule
```

## Explainability

Every important action records:

- What changed
- Previous schedule
- New schedule
- Why it changed
- Which rules or priorities influenced it
- Whether user approval was required

## Behavioral Learning

ChronoMind learns patterns from:

- Planned vs actual completion
- Preferred working hours
- Repeated postponements
- User edits to AI plans
- Accepted suggestions
- Rejected suggestions
- Estimated vs actual duration
- Task category
- Day of week

V2 begins with statistics and preference learning.

Full reinforcement learning is **not required** for the first V2 implementation.

Later experiments may use ranking models or contextual bandits.

---

# 4. Core Engineering Principle

ChronoMind is a **hybrid AI system**.

Do not use an LLM for deterministic problems.

```text
LangGraph
    ↓
Workflow orchestration + state

Python algorithms
    ↓
Scheduling + validation + priority scoring + constraints

LLMs
    ↓
Ambiguity + reasoning + decomposition + explanations

PostgreSQL
    ↓
Tasks + goals + behavior + decisions + durable graph state

User
    ↓
Control over important decisions
```

This architecture is cheaper, faster, easier to test, and more reliable than putting an LLM inside every node.

---

# 5. Complete System Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                             USER                                    │
│                                                                     │
│             Manual UI       Text Chat       Voice Input             │
└─────────────────┬──────────────┬────────────────┬────────────────────┘
                  │              │                │
                  └──────────────┼────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                    │
│                                                                     │
│ React + Vite + TypeScript                                           │
│ Tailwind CSS                                                        │
│ TanStack Query → server state                                       │
│ Zustand → local/UI state                                            │
│ Firebase Auth                                                       │
│ Web Speech API → zero-cost voice-first path                         │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ HTTPS + Firebase ID Token
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI API                                 │
│                                                                     │
│ Authentication                                                      │
│ Task / Goal / Profile APIs                                          │
│ Assistant API                                                       │
│ Planning API                                                        │
│ Approval API                                                        │
│ Analytics / Stats API                                               │
└───────────────┬───────────────────────────┬─────────────────────────┘
                │                           │
                ▼                           ▼
┌────────────────────────────┐   ┌────────────────────────────────────┐
│    DOMAIN SERVICES         │   │       CHRONOMIND PLANNER          │
│                            │   │                                    │
│ Task Service               │   │ LangGraph StateGraph               │
│ Goal Service               │   │                                    │
│ Calendar Service           │   │ Context → Priority → Schedule      │
│ Behavior Service           │   │ → Split → Validate → Evaluate      │
│ Notification Service       │   │ → Replan → Approval → Execute      │
│ Decision Log Service       │   │                                    │
└──────────────┬─────────────┘   └──────────────┬─────────────────────┘
               │                                │
               │                                ▼
               │                     ┌──────────────────────────────┐
               │                     │       TOOL LAYER             │
               │                     │                              │
               │                     │ create_task                  │
               │                     │ update_task                  │
               │                     │ query_tasks                  │
               │                     │ calculate_free_slots         │
               │                     │ calculate_priority           │
               │                     │ split_task                   │
               │                     │ validate_schedule            │
               │                     │ move_task                    │
               │                     │ get_user_context             │
               │                     └────────────┬─────────────────┘
               │                                  │
               ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                │
│                                                                     │
│ PostgreSQL                                                          │
│ ├── users                                                           │
│ ├── tasks                                                           │
│ ├── goals                                                           │
│ ├── user_preferences                                                │
│ ├── behavior_events                                                 │
│ ├── planning_decisions                                              │
│ ├── agent_runs                                                      │
│ ├── notifications                                                   │
│ └── LangGraph checkpoint tables                                     │
│                                                                     │
│ Firebase Authentication → identity only                             │
│ Optional pgvector → future semantic memory / RAG                    │
└─────────────────────────────────────────────────────────────────────┘

                    AI / LLM LAYER

            Model Router
                 │
      ┌──────────┼────────────┐
      │          │            │
 No LLM      Fast Model   Reasoning Model
      │          │            │
 Rules       parsing /      difficult
 math        extraction     planning
 validation categorization  decomposition
```

---

# 6. Recommended Technology Stack

## Frontend

| Concern | Technology |
|---|---|
| UI | React |
| Build tool | Vite |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Routing | React Router |
| Server-state fetching/cache | TanStack Query |
| Local/UI state | Zustand |
| HTTP client | Axios or native fetch |
| Dates | date-fns |
| Drag/drop | dnd-kit |
| Animations | Framer Motion |
| Icons | Lucide React |
| Authentication | Firebase Auth |
| Voice input | Web Speech API |
| Unit/component tests | Vitest + Testing Library |
| E2E tests | Playwright |

### State rule

Use:

```text
TanStack Query → data coming from backend

Zustand → UI state only
```

Do not duplicate backend task data in multiple stores unless there is a clear reason.

## Backend

| Concern | Technology |
|---|---|
| API | FastAPI |
| Language | Python 3.12+ |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2 |
| Database migrations | Alembic |
| PostgreSQL driver | Psycopg 3 / async driver |
| Agent workflow | LangGraph |
| Agent persistence | langgraph-checkpoint-postgres |
| LLM provider | Groq through provider adapter |
| Retries | LangGraph retry policy and/or Tenacity where appropriate |
| HTTP calls | HTTPX |
| Auth verification | Firebase Admin SDK |
| Testing | pytest + pytest-asyncio |
| Linting | Ruff |
| Type checking | mypy or pyright |
| Environment management | pyproject.toml + uv |
| Agent tracing/evaluation | LangSmith |
| App logs | Python structured logging |

Do not hard-code a specific model throughout the application.

Use environment configuration:

```text
LLM_FAST_MODEL=
LLM_REASONING_MODEL=
LLM_FALLBACK_MODEL=
```

---

# 7. Storage Architecture

## V2 Storage Decision

V2 should use:

```text
Firebase Auth
      ↓
identity

PostgreSQL
      ↓
all persistent application data
+
LangGraph durable checkpoints
```

Firestore was appropriate for the first version, but ChronoMind V2 benefits from PostgreSQL because scheduling and agent systems need:

- Transactions
- Strong relational integrity
- Efficient date/time queries
- Analytics
- Decision history
- Behavior-event analysis
- Concurrency control
- Durable LangGraph checkpoints
- Easier migration/versioning of schemas

### Important

Do not permanently maintain Firestore and PostgreSQL as two sources of truth.

Migration approach:

```text
V1 Firestore
    ↓
one-time migration script
    ↓
PostgreSQL
    ↓
V2 source of truth
```

Firebase Auth remains unchanged.

---

# 8. Core Database Schema

## `users`

```text
id UUID PRIMARY KEY
firebase_uid TEXT UNIQUE NOT NULL
email TEXT
display_name TEXT
timezone TEXT DEFAULT 'Asia/Kolkata'
created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

The user timezone must be explicit.

Never depend on server-local `date.today()` for user scheduling.

## `tasks`

```text
id UUID PRIMARY KEY
user_id UUID FK users.id

title TEXT NOT NULL
description TEXT
category TEXT

status:
    pending
    in_progress
    completed
    skipped
    cancelled

source:
    manual
    chat
    voice
    agent

start_at TIMESTAMPTZ
end_at TIMESTAMPTZ
deadline_at TIMESTAMPTZ NULL

estimated_duration_minutes INTEGER

manual_priority SMALLINT        # 1–5
computed_priority NUMERIC
priority_reason JSONB

flexibility:
    fixed
    flexible
    highly_flexible

splittable BOOLEAN
is_user_locked BOOLEAN

parent_task_id UUID NULL
segment_index INTEGER NULL

recurrence_rule TEXT NULL       # Prefer RRULE-compatible representation

reschedule_count INTEGER DEFAULT 0
last_rescheduled_at TIMESTAMPTZ NULL

completed_at TIMESTAMPTZ NULL

created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Store real timestamps rather than independent date/time strings.

Store in UTC; convert using the user's timezone at application boundaries.

## `goals`

Represents what is currently important to the user.

```text
id UUID PRIMARY KEY
user_id UUID

title TEXT
category TEXT

weight NUMERIC

active_from TIMESTAMPTZ
active_until TIMESTAMPTZ NULL

status:
    active
    paused
    completed

created_at TIMESTAMPTZ
updated_at TIMESTAMPTZ
```

Example:

```text
Goal: Placement Preparation
Weight: 1.5

Related categories:
DSA
Aptitude
Interview Preparation
```

## `user_preferences`

```text
user_id UUID PRIMARY KEY

preferred_focus_windows JSONB
preferred_break_minutes INTEGER
max_daily_focus_minutes INTEGER

category_preferences JSONB
day_preferences JSONB

auto_apply_low_impact_changes BOOLEAN
approval_threshold NUMERIC

behavior_profile JSONB

updated_at TIMESTAMPTZ
```

## `behavior_events`

Append-only behavior log.

```text
id UUID PRIMARY KEY
user_id UUID
task_id UUID NULL

event_type:
    task_created
    task_started
    task_completed
    task_skipped
    task_rescheduled
    ai_plan_accepted
    ai_plan_rejected
    ai_plan_modified

event_data JSONB

created_at TIMESTAMPTZ
```

Do not continuously rewrite historical behavior.

Record events and derive behavior features from them.

## `planning_decisions`

Stores explainability and audit history.

```text
id UUID PRIMARY KEY
user_id UUID
agent_run_id UUID
task_id UUID NULL

action:
    schedule
    reschedule
    split
    keep
    propose
    cancel_proposal

old_state JSONB
new_state JSONB

reason_codes JSONB
explanation TEXT NULL

confidence NUMERIC

approval_required BOOLEAN
approval_status:
    not_required
    pending
    accepted
    rejected
    modified

created_at TIMESTAMPTZ
```

## `agent_runs`

Used for AI engineering observability.

```text
id UUID PRIMARY KEY
user_id UUID

trigger_type TEXT
status TEXT

replan_count INTEGER

llm_call_count INTEGER
input_tokens INTEGER
output_tokens INTEGER
estimated_cost NUMERIC

latency_ms INTEGER

error_code TEXT NULL
error_message TEXT NULL

started_at TIMESTAMPTZ
finished_at TIMESTAMPTZ
```

## `notifications`

```text
id UUID PRIMARY KEY
user_id UUID

type TEXT
title TEXT
message TEXT
metadata JSONB

read BOOLEAN DEFAULT FALSE

created_at TIMESTAMPTZ
```

---

# 9. LangGraph Persistence

ChronoMind requires durable graph state because human approval may pause execution.

Use:

```text
langgraph-checkpoint-postgres
```

Development:

```text
SQLite/InMemory checkpointer may be used locally
```

Production:

```text
AsyncPostgresSaver
```

Each planning execution should have a thread/run identifier.

Example:

```text
thread_id = planning:{user_id}:{agent_run_id}
```

The graph must be able to:

- Save state
- Pause
- Resume
- Survive backend restart
- Continue after human approval

---

# 10. LangGraph Planning Architecture

Use **one primary planning graph**, not many autonomous agents.

```text
START
  │
  ▼
load_context
  │
  ▼
understand_trigger
  │
  ▼
update_goal_context
  │
  ▼
calculate_priorities
  │
  ▼
build_candidate_schedule
  │
  ▼
evaluate_task_splitting
  │
  ▼
validate_schedule
  │
  ├──────── valid ────────► evaluate_plan_quality
  │
  └──────── invalid ──────► replan
                               │
                               └──────► validate_schedule

evaluate_plan_quality
  │
  ▼
determine_human_approval
  │
  ├── low impact ─────────► execute_plan
  │
  └── high impact ────────► human_approval
                                │
                       ┌────────┴────────┐
                       │                 │
                    accept            modify
                       │                 │
                       ▼                 ▼
                  execute_plan        replan

execute_plan
  │
  ▼
record_decisions
  │
  ▼
generate_explanation_if_needed
  │
  ▼
END
```

Behavior learning runs after user events and feeds the next planning cycle.

---

# 11. LangGraph State

Example:

```python
class ChronoMindState(TypedDict):
    user_id: str
    agent_run_id: str

    trigger_type: str
    trigger_data: dict

    now_utc: str
    user_timezone: str

    tasks: list
    fixed_events: list
    unfinished_tasks: list

    active_goals: list
    user_preferences: dict
    behavior_profile: dict

    priority_scores: dict

    candidate_plan: list
    split_proposals: list

    validation_result: dict
    plan_quality: dict

    replan_count: int
    max_replans: int

    approval_required: bool
    approval_payload: dict | None
    user_feedback: dict | None

    final_plan: list
    decisions: list

    llm_usage: dict
    errors: list
```

Nodes should update only the state fields they own.

---

# 12. Graph Triggers

The graph may run when:

```text
NEW_TASK
TASK_UPDATED
TASK_COMPLETED
TASK_MISSED
DEADLINE_CHANGED
GOAL_CHANGED
PRIORITY_CHANGED
CALENDAR_CHANGED
DAILY_PLAN
END_OF_DAY_REVIEW
MANUAL_REPLAN
HUMAN_FEEDBACK
```

Not every trigger requires the entire graph.

Conditional routing should skip unnecessary nodes.

Example:

```text
Task title edit
→ no full replan

New fixed 3-hour event tomorrow
→ full schedule re-evaluation
```

---

# 13. Priority Engine

Priority calculation should be deterministic and explainable.

Initial formula:

```text
priority_score =
      W1 × manual_priority
    + W2 × deadline_urgency
    + W3 × goal_relevance
    + W4 × postponement_pressure
    + W5 × dependency_importance
    + W6 × context_relevance
    + W7 × behavior_fit
```

Normalize values to a known range.

Example:

```text
Task: DSA Arrays Practice

manual priority       0.90
deadline urgency      0.60
goal relevance        1.00
postponement pressure 0.20
behavior fit          0.80
```

Store both:

```text
computed_priority
priority_reason
```

so the UI can explain the result.

## Context Multiplier

Example:

```text
placement_season:

DSA                    × 1.50
Aptitude               × 1.40
Interview Prep         × 1.40
College Coursework     × 1.00
Entertainment          × 0.50
```

These weights are suggestions, not universal truths.

Users can modify them.

---

# 14. Scheduler / Constraint Engine

Scheduling is deterministic.

Suggested algorithm for first V2:

```text
1. Load fixed events
2. Load user-locked tasks
3. Calculate free intervals
4. Sort flexible tasks by priority score
5. Place deadline-critical tasks first
6. Respect preferred focus windows where possible
7. Fit normal flexible tasks
8. Attempt splitting when needed
9. Validate entire plan
10. Calculate quality score
```

A sophisticated optimization solver is not required initially.

A well-tested greedy heuristic is sufficient for V2.

If later necessary, the scheduler can be upgraded to:

```text
Google OR-Tools CP-SAT
```

without changing the LangGraph architecture.

---

# 15. Schedule Validator

Every candidate schedule must pass deterministic validation.

Check:

```text
No task overlap
No fixed-event overlap
No invalid timestamps
No end-before-start
No duplicated placement
No scheduling outside configured hours
No deadline violation where avoidable
No user-locked task movement
No dependency violation
No duplicate task segment
No excessive split count
No impossible duration
```

The validator is the authority.

The LLM cannot override it.

---

# 16. Replanning Strategy

If validation fails:

```text
attempt 1
   ↓
identify conflicts
   ↓
modify placement strategy
   ↓
attempt 2
```

Maximum:

```text
MAX_REPLANS = 3
```

If still unsuccessful:

```text
return best alternatives
+
ask user
```

Never allow unbounded LangGraph cycles.

---

# 17. Task Splitting

A task may be split only when:

```text
splittable = true
```

Rule-first approach:

```text
if duration > largest_free_slot:
    attempt deterministic segmentation
```

For generic work:

```text
3 hours
→ 3 × 1-hour blocks
```

For semantically meaningful tasks:

```text
"Prepare project presentation"
```

LLM may propose:

```text
Research
Outline
Create slides
Review
```

The schedule validator still decides whether those segments can fit.

---

# 18. Human-in-the-Loop Policy

## Auto-apply

Examples:

```text
Move flexible task by 30 minutes
Move optional task inside same day
Choose another equivalent free slot
```

## Approval required

Examples:

```text
Move task to another day
Move deadline-critical work
Change multiple tasks
Split an important task
Remove a planned leisure block
Modify user-locked schedule
Large change to tomorrow
```

Implement the pause using LangGraph interrupt/resume.

Frontend receives a proposal:

```json
{
  "proposal_id": "...",
  "summary": "3 tasks need to move to preserve your assignment deadline.",
  "changes": [],
  "options": ["accept", "modify", "reject"]
}
```

---

# 19. Assistant Architecture

The assistant is not a separate uncontrolled agent.

It is an interface to ChronoMind tools and the planning graph.

```text
User message
      ↓
Intent parser
      ↓
Structured action
      ↓
Permission / validation
      ↓
Tool call or planner invocation
      ↓
Result
      ↓
Natural-language response
```

Supported tools should include:

```text
create_task
update_task
complete_task
delete_task
query_tasks
query_goals
create_goal
update_goal
find_free_slots
request_replan
get_schedule
get_planning_explanation
```

---

# 20. Structured Outputs — No Regex Parsing

V1 currently asks the model to emit text plus JSON and extracts actions using regex.

V2 must replace that pattern.

Use:

```text
Pydantic schemas
+
provider structured outputs / tool calling
```

Example:

```python
class CreateTaskAction(BaseModel):
    action: Literal["create_task"]
    title: str
    start_at: datetime
    end_at: datetime
    manual_priority: int
```

LLM output is parsed into a validated object before any tool executes.

The model never directly writes to the database.

---

# 21. LLM Model Router

Do not send every request to a large reasoning model.

```text
incoming request
      ↓
complexity router
      ↓
┌─────────────┬──────────────┬──────────────────┐
│ No LLM      │ Fast Model   │ Reasoning Model  │
│             │              │                  │
│ math        │ intent       │ hard replanning  │
│ validation  │ extraction   │ goal conflicts   │
│ free slots  │ categories   │ decomposition    │
│ scoring     │ simple chat  │ complex choices  │
└─────────────┴──────────────┴──────────────────┘
```

## No-LLM tasks

```text
priority math
free-slot calculations
overlap checking
deadline checking
database operations
behavior statistics
schedule validation
```

## Fast model

```text
intent classification
task extraction
simple categorization
short user-facing replies
```

## Reasoning model

```text
complex multi-goal planning
ambiguous priority decisions
semantic task decomposition
difficult replanning
```

All model IDs live in environment variables.

---

# 22. LLM Cost Controls

Every LLM call should have a reason.

Use:

```text
structured context
small relevant task windows
history summarization
model routing
response token limits
prompt caching where supported
no repeated full-calendar prompts
deterministic pre-processing
LLM fallback only when ambiguity exists
```

Record per run:

```text
model
input tokens
output tokens
latency
estimated cost
success/failure
```

The goal is not "zero LLM calls."

The goal is:

> **Use LLM intelligence only where it provides value.**

---

# 23. Voice Architecture

V2 should keep voice simple.

Primary path:

```text
Microphone
   ↓
Browser Web Speech API
   ↓
Transcript
   ↓
Assistant intent parser
   ↓
Structured action
   ↓
Planner / task tool
```

This path has no additional speech API cost.

Optional fallback adapter:

```text
Audio
 ↓
server STT provider
 ↓
transcript
```

Keep speech-to-text behind an interface so the provider can change later.

Do not make the planning architecture dependent on one speech provider.

---

# 24. Behavior Learning Architecture

```text
User action
     ↓
behavior event
     ↓
feature aggregation
     ↓
behavior profile
     ↓
priority engine
     +
scheduler
     ↓
new plan
     ↓
user accepts / edits / rejects
     ↓
new behavior event
```

Initial features:

```text
completion rate by category
completion rate by time window
average duration error
reschedule rate
preferred focus windows
AI proposal acceptance rate
manual edit patterns
```

Example:

```text
DSA completion:
morning → 45%
evening → 82%

Future preference:
prefer DSA in evening when constraints permit
```

The user can override learned preferences.

---

# 25. Explainability Architecture

Prefer structured reason codes.

Example:

```json
{
  "decision": "reschedule",
  "task_id": "...",
  "reason_codes": [
    "PLACEMENT_GOAL_HIGH",
    "DEADLINE_PRESSURE",
    "EVENING_BEHAVIOR_MATCH",
    "FREE_SLOT_AVAILABLE"
  ]
}
```

Natural-language explanation should be generated only when:

- User asks "why?"
- Change is high impact
- Notification needs an explanation

This saves tokens.

---

# 26. AI Observability

Each planning run should be traceable.

Example developer trace:

```text
RUN: 01J...
Trigger: TASK_MISSED

load_context            48 ms
calculate_priorities    11 ms

candidate_plan #1
validator → FAILED
reason → LAB_CONFLICT

replan #1
candidate_plan #2
validator → PASSED

human approval → not required
execute → success

LLM calls → 1
input tokens → 510
output tokens → 96
total latency → 1.2 s
```

Use:

```text
LangSmith → LangGraph/LLM tracing and evaluations
agent_runs table → product-level metrics
structured backend logs → application debugging
```

---

# 27. Evaluation Architecture

An AI engineer must prove that the agent works.

Create:

```text
evals/scenarios.jsonl
```

Each scenario contains:

```json
{
  "name": "placement priority conflict",
  "user_context": {},
  "tasks": [],
  "trigger": {},
  "expected_constraints": {}
}
```

Build at least 100 representative cases over time.

Evaluate:

```text
intent extraction accuracy
tool selection accuracy
schedule validity rate
task overlap rate
deadline violation rate
priority adherence
replanning success rate
task splitting validity
human-approval policy accuracy
explanation grounding
latency
LLM calls per planning run
tokens per planning run
estimated cost per planning run
```

Regression tests should run before merging agent changes.

---

# 28. Backend Architecture

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── tasks.py
│   │   ├── goals.py
│   │   ├── assistant.py
│   │   ├── planning.py
│   │   ├── approvals.py
│   │   ├── notifications.py
│   │   └── profile.py
│   │
│   ├── agents/
│   │   ├── planning_graph.py
│   │   ├── state.py
│   │   ├── routing.py
│   │   └── checkpoints.py
│   │
│   ├── planning/
│   │   ├── priority_engine.py
│   │   ├── free_slots.py
│   │   ├── scheduler.py
│   │   ├── task_splitter.py
│   │   ├── validator.py
│   │   └── plan_evaluator.py
│   │
│   ├── llm/
│   │   ├── provider.py
│   │   ├── model_router.py
│   │   ├── schemas.py
│   │   ├── intent_parser.py
│   │   ├── decomposition.py
│   │   └── explanation.py
│   │
│   ├── tools/
│   │   ├── task_tools.py
│   │   ├── goal_tools.py
│   │   ├── calendar_tools.py
│   │   └── planning_tools.py
│   │
│   ├── behavior/
│   │   ├── events.py
│   │   ├── features.py
│   │   └── profile.py
│   │
│   ├── services/
│   │   ├── task_service.py
│   │   ├── goal_service.py
│   │   ├── planning_service.py
│   │   ├── notification_service.py
│   │   └── decision_service.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── models/
│   │   └── repositories/
│   │
│   ├── auth/
│   │   └── firebase.py
│   │
│   └── core/
│       ├── config.py
│       ├── logging.py
│       └── exceptions.py
│
├── migrations/
├── tests/
├── evals/
├── scripts/
├── pyproject.toml
└── .env.example
```

---

# 29. Frontend Architecture

```text
frontend/
│
├── src/
│   ├── app/
│   │   ├── router.tsx
│   │   └── providers.tsx
│   │
│   ├── pages/
│   │   ├── Dashboard/
│   │   ├── Calendar/
│   │   ├── Goals/
│   │   ├── Insights/
│   │   └── Profile/
│   │
│   ├── features/
│   │   ├── tasks/
│   │   ├── assistant/
│   │   ├── planning/
│   │   ├── approvals/
│   │   ├── calendar/
│   │   ├── goals/
│   │   ├── behavior/
│   │   └── notifications/
│   │
│   ├── components/
│   │   ├── ui/
│   │   └── layout/
│   │
│   ├── api/
│   │   ├── client.ts
│   │   ├── tasks.ts
│   │   ├── planning.ts
│   │   └── assistant.ts
│   │
│   ├── store/
│   │   └── uiStore.ts
│   │
│   ├── auth/
│   │   └── firebase.ts
│   │
│   ├── types/
│   └── utils/
│
├── tests/
└── package.json
```

## Main V2 UI Components

```text
TaskCard
TaskEditor
GoalManager
PriorityReasonPopover
PlanningProposal
PlanChangeDiff
ApprovalPanel
AssistantPanel
VoiceButton
BehaviorInsights
AgentRunStatus
CalendarDay
CalendarWeek
CalendarMonth
FocusTimer
NotificationCenter
```

---

# 30. API Architecture

Suggested routes:

```text
GET    /api/tasks
POST   /api/tasks
PATCH  /api/tasks/{id}
DELETE /api/tasks/{id}
POST   /api/tasks/{id}/complete

GET    /api/goals
POST   /api/goals
PATCH  /api/goals/{id}

POST   /api/assistant/message

POST   /api/planning/replan
GET    /api/planning/runs/{run_id}
GET    /api/planning/decisions/{decision_id}

POST   /api/approvals/{run_id}/accept
POST   /api/approvals/{run_id}/modify
POST   /api/approvals/{run_id}/reject

GET    /api/notifications
PATCH  /api/notifications/{id}/read

GET    /api/profile
GET    /api/insights
```

Internal scheduled route or script:

```text
daily planning trigger
end-of-day trigger
behavior aggregation
```

---

# 31. Scheduling / Background Jobs

Do not run production-critical schedules only inside the FastAPI web process.

V1 currently uses APScheduler inside the backend process.

This can miss jobs during:

- Deployments
- Server sleep
- Restarts

and can duplicate jobs when multiple application workers exist.

V2 production design:

```text
Managed Cron / Scheduler
        ↓
authenticated internal planning job
        ↓
FastAPI planning service
        ↓
LangGraph
```

For local development:

```text
APScheduler is acceptable
```

For production:

```text
Render Cron Job
or equivalent managed scheduler
```

If V2 later needs a durable asynchronous queue, introduce Redis + RQ/Arq/Dramatiq only then.

**Redis is intentionally not required in the initial architecture.**

---

# 32. Authentication and Authorization

Keep Firebase Authentication.

Flow:

```text
Browser
  ↓
Firebase login
  ↓
ID token
  ↓
Authorization: Bearer <token>
  ↓
FastAPI
  ↓
Firebase Admin verifies token
  ↓
firebase_uid
  ↓
PostgreSQL user mapping
```

Every query must scope data by authenticated `user_id`.

Never trust user IDs sent in request bodies.

---

# 33. Security / Guardrails

The planning agent must never have unrestricted database access.

All actions go through validated tools.

Rules:

```text
Never silently delete important user work
Never move user-locked tasks
Never create overlapping tasks
Never execute invalid model output
Never trust model-generated IDs without ownership checks
Never allow infinite replanning
Never expose service credentials
Never place Firebase service-account JSON in the repository
Never log sensitive tokens
Always preserve decision history
Always provide undo for agent schedule changes
```

Low-priority unfinished tasks should be moved to backlog/skipped/cancelled status rather than silently deleted by default.

---

# 34. Timezone Strategy

V1 uses string dates/times and server date functions in several places.

V2 rule:

```text
Database → UTC TIMESTAMPTZ

User profile → IANA timezone

Frontend → user-local rendering

Planner → convert to user timezone for daily scheduling

Backend → timezone-aware datetime only
```

Avoid naive datetimes.

---

# 35. Recurrence Strategy

Replace custom recurrence strings as the long-term representation with an RRULE-compatible recurrence model.

Examples:

```text
Every day
Every Monday
Monday, Wednesday, Friday
Every weekday
```

Recurring tasks should have:

```text
series_id
recurrence_rule
instance date/time
exception handling
```

Do not create duplicate future instances.

---

# 36. Known V1 Issues to Fix During Migration

Before considering V2 stable, address the following behaviors observed in the current repository.

## Future-slot collision

The existing rescheduler independently calculates future free slots for each task.

Two rescheduled tasks can therefore potentially select the same future slot.

V2 solves this by building one candidate schedule in memory and validating it before writing.

## Look-ahead date gap

The existing fallback calculates future dates from `tomorrow` while starting at offset `2`.

That skips the day immediately after tomorrow.

V2 centralizes all date arithmetic in timezone-aware scheduling utilities.

## Date-only task update conflict

The existing update service performs conflict checks when start/end time changes, but changing only the date can bypass the conflict check.

V2 validates the complete resulting task interval on every schedule-affecting update.

## Regex LLM actions

The current assistant extracts JSON actions from model text using regex.

V2 uses schema-constrained structured output/tool calling.

## Night scheduler reliability

The current scheduler runs inside FastAPI.

V2 uses a managed scheduler for production.

## Silent deletion of low-priority unfinished tasks

V2 should not delete user work merely because it is low priority.

Use:

```text
backlog
skipped
cancelled
```

with explainable policy.

## Sparse tests

The current tests cover only basic API validation.

V2 requires:

```text
unit tests
integration tests
agent graph tests
scheduler tests
concurrency tests
evaluation scenarios
frontend component tests
E2E tests
```

## Daily briefing integration

The current dashboard asks the assistant for a morning briefing while the assistant system prompt restricts it to scheduling/query operations.

V2 makes briefing a supported intent or separate deterministic summary endpoint.

---

# 37. Testing Strategy

## Unit tests

Test:

```text
priority formula
free-slot calculations
overlap detection
task splitting
timezone conversion
recurrence
plan quality
approval classification
behavior features
```

## Integration tests

Test:

```text
API + database
Firebase token middleware mocks
LLM structured-output parser
planning graph + Postgres checkpoint
human interrupt/resume
```

## Agent tests

Test graph transitions:

```text
valid first plan
invalid → replan
high impact → approval
approval → resume
rejection → no write
max replan reached
LLM failure fallback
```

## End-to-end

Use Playwright:

```text
login
create task
voice/text task command
request replan
approve proposal
verify calendar update
complete task
view explanation
```

---

# 38. Failure Handling

Every external call needs a failure policy.

Example:

```text
LLM timeout
   ↓
retry limited times
   ↓
fallback model if configured
   ↓
deterministic-safe response
```

If planning cannot complete:

```text
Do not partially write the plan.

Return:
"ChronoMind could not safely apply this plan."
```

Execution writes should use transactions where multiple changes must succeed together.

---

# 39. Deployment Architecture

Recommended simple deployment:

```text
GitHub
  │
  ├─────────────► Vercel
  │                ↓
  │              React
  │
  └─────────────► Render
                   ↓
                 FastAPI
                   │
        ┌──────────┼────────────┐
        │          │            │
        ▼          ▼            ▼
   PostgreSQL   Groq API    Firebase Auth

Managed Cron
    ↓
Planning Trigger
    ↓
FastAPI / worker entrypoint
```

Use any managed PostgreSQL provider.

The architecture should not depend on one database vendor.

---

# 40. Environment Variables

Backend:

```bash
APP_ENV=development

DATABASE_URL=

FIREBASE_SERVICE_ACCOUNT_JSON=

GROQ_API_KEY=

LLM_FAST_MODEL=
LLM_REASONING_MODEL=
LLM_FALLBACK_MODEL=

LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=chronomind-v2

CORS_ORIGINS=http://localhost:5173

DEFAULT_TIMEZONE=Asia/Kolkata

MAX_REPLAN_ATTEMPTS=3
AUTO_APPLY_LOW_IMPACT=true
```

Frontend:

```bash
VITE_API_URL=http://localhost:8000

VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=
VITE_FIREBASE_APP_ID=
```

Never commit real `.env` files.

---

# 41. Development Setup

## Backend

```bash
cd backend

uv sync

cp .env.example .env

alembic upgrade head

uv run uvicorn app.main:app --reload --port 8000
```

## Frontend

```bash
cd frontend

npm install

cp .env.example .env

npm run dev
```

---

# 42. V1 → V2 Migration Plan

```text
STEP 1
Freeze and document current V1 behavior.

STEP 2
Create PostgreSQL schema + Alembic migrations.

STEP 3
Write Firestore → PostgreSQL migration script.

STEP 4
Move task CRUD to repository/service architecture.

STEP 5
Fix scheduling correctness and timezone handling.

STEP 6
Replace regex LLM actions with structured tool calls.

STEP 7
Create priority engine.

STEP 8
Create deterministic schedule builder + validator.

STEP 9
Build new LangGraph planning graph.

STEP 10
Add Postgres checkpoint persistence.

STEP 11
Add adaptive rescheduling + replanning.

STEP 12
Add task splitting.

STEP 13
Add human approval interrupt/resume.

STEP 14
Add decision logging + explanations.

STEP 15
Add behavior event tracking.

STEP 16
Add behavior-derived preferences.

STEP 17
Add model router + token/cost telemetry.

STEP 18
Add evaluation dataset and regression suite.

STEP 19
Add agent observability dashboard/trace links.

STEP 20
Replace in-process production scheduler with managed cron.

STEP 21
Run V1/V2 migration verification.

STEP 22
Remove Firestore task storage after successful migration.
```

---

# 43. Implementation Phases

## Phase A — Reliability Foundation

Build:

```text
PostgreSQL
SQLAlchemy
Alembic
timezone-safe task model
repository pattern
validation
tests
```

No advanced AI yet.

## Phase B — Planning Engine

Build:

```text
priority engine
free-slot engine
schedule builder
validator
plan evaluator
```

## Phase C — Agentic Workflow

Build:

```text
LangGraph state
graph routing
replanning
checkpoint persistence
human approval
```

## Phase D — LLM Intelligence

Build:

```text
structured intent parsing
tool calling
task decomposition
model router
explanation generator
```

## Phase E — Personalization

Build:

```text
behavior events
behavior features
user preference profile
adaptive scheduling
```

## Phase F — Production AI Engineering

Build:

```text
evaluation suite
LangSmith traces
token/cost metrics
latency metrics
failure recovery
CI
E2E tests
```

---

# 44. AI Engineer Skills Demonstrated

ChronoMind V2 should demonstrate practical capability in:

```text
LLM integration
prompt/context engineering
structured outputs
tool/function calling
agentic AI
LangGraph
stateful workflows
human-in-the-loop
memory/personalization
planning and replanning
optimization
ranking/prioritization
voice AI integration
backend API design
database design
model routing
LLM cost optimization
agent evaluation
observability
guardrails
fallback design
testing
MLOps / deployment
feedback learning
```

The project should prove these through working architecture and measurable results, not by adding unnecessary buzzwords.

---

# 45. Optional Future Extensions

These are deliberately outside the core V2 implementation.

## OR-Tools Schedule Optimization

Replace or augment the greedy scheduler with CP-SAT when constraint complexity justifies it.

## Contextual Bandit / Preference Learning

Use accept/reject behavior to improve scheduling decisions.

Start only after sufficient real feedback data exists.

## Semantic Long-Term Memory

Use pgvector for semantic retrieval if structured preference data becomes insufficient.

Do not use embeddings for information that belongs in normal relational columns.

## ChronoMind Developer RAG Assistant

A separate developer assistant may answer questions about the codebase using curated project documentation.

Recommended corpus:

```text
README.md
docs/architecture.md
docs/agent-workflow.md
docs/storage.md
docs/api.md
```

Prefer curated documentation over blindly embedding the entire repository.

## Timetable Import

Add OCR/document parsing later for importing college timetables.

Pipeline:

```text
image/PDF
  ↓
OCR/parser
  ↓
structured timetable
  ↓
user verification
  ↓
calendar events
```

Do not automatically trust OCR output without confirmation.

---

# 46. Future Advanced Evolution — What We Add Later and Why

The technologies below are **not rejected**. They are deliberately kept outside the core V2 build because they solve problems that appear only after ChronoMind grows in users, traffic, data, integrations, or AI complexity.

The rule is:

> **Build the simplest reliable architecture first. Add distributed or advanced AI infrastructure only when a measurable requirement justifies it.**

---

## 46.1 Redis — Cache, Distributed Locks, and Fast Ephemeral State

### Purpose

Redis is useful when ChronoMind needs very fast temporary shared state.

Possible uses:

```text
API response caching
rate-limit counters
distributed locks
temporary planning-session state
frequently accessed user preference cache
background-job coordination
short-lived notification state
```

### Example

If several workers try to replan the same user's schedule at the same time:

```text
planning request A
planning request B
        ↓
Redis distributed lock
        ↓
only one planner modifies the schedule
```

### When to add it

Add Redis when:

```text
multiple backend workers are running
duplicate planning jobs become possible
database reads become expensive
background queues need a broker
high request traffic makes caching useful
```

### Why not in core V2?

PostgreSQL and LangGraph checkpoints are enough for the first production architecture.

Adding Redis immediately creates another system to deploy, secure, monitor, and keep consistent.

---

## 46.2 Background Job Queue

Core V2 can use a managed cron for scheduled planning.

At larger scale introduce a durable queue.

Possible technologies:

```text
Redis + RQ
Redis + Dramatiq
Redis + Arq
Celery
cloud-managed queue
```

### Purpose

Move long-running work away from API request threads.

Examples:

```text
weekly replanning
behavior aggregation
large timetable imports
evaluation runs
batch notifications
LLM-heavy decomposition
calendar synchronization
```

Architecture:

```text
FastAPI
   ↓
enqueue job
   ↓
Queue
   ↓
Worker
   ↓
LangGraph / service
   ↓
PostgreSQL
```

### When to add it

Add when operations become too slow or unreliable to perform during normal HTTP requests.

---

## 46.3 Kafka / Event Streaming

Kafka is **not required for V2**.

### Purpose

Kafka becomes useful when ChronoMind evolves into a distributed system where many independent services consume large numbers of events.

Example events:

```text
TASK_CREATED
TASK_COMPLETED
TASK_RESCHEDULED
PLAN_ACCEPTED
PLAN_REJECTED
GOAL_CHANGED
CALENDAR_UPDATED
VOICE_COMMAND_RECEIVED
```

Possible future architecture:

```text
ChronoMind services
       ↓
event stream
       ↓
Kafka
 ├── Behavior Analytics
 ├── Notification Service
 ├── Recommendation System
 ├── Data Warehouse
 ├── Evaluation Pipeline
 └── Personalization Pipeline
```

### When Kafka makes sense

Only when:

```text
traffic is high
many independent consumers need the same events
event replay is valuable
services need asynchronous communication
analytics pipelines operate continuously
```

### Why not now?

For V2:

```text
PostgreSQL behavior_events
+
normal application events
```

are sufficient.

Kafka would add infrastructure without improving the current user experience.

---

## 46.4 Microservices

ChronoMind V2 should begin as a **modular monolith**.

```text
one FastAPI application
        ↓
clear internal modules
```

Future services might become:

```text
Planning Service
Assistant Service
Notification Service
Behavior / Personalization Service
Calendar Integration Service
Voice Service
Evaluation Service
```

### Purpose

Microservices help when different parts of the system need:

```text
independent scaling
independent deployments
different infrastructure
different reliability requirements
separate engineering ownership
```

### When to split

Only split a module when there is evidence that it needs independent operation.

Example:

```text
Assistant traffic grows 20×
while
planning jobs remain relatively small
```

Then the assistant may become its own service.

### Why not now?

A modular monolith is:

```text
easier to build
easier to debug
easier to test
cheaper to host
easier to understand in interviews
```

Good module boundaries today make future extraction into services straightforward.

---

## 46.5 Kubernetes

Kubernetes is an infrastructure orchestration platform.

### Future purpose

If ChronoMind eventually runs many containers/services, Kubernetes could manage:

```text
service deployment
horizontal scaling
load balancing
rolling updates
health checks
service discovery
worker pools
configuration
resilience
```

Future example:

```text
Kubernetes Cluster

├── API Pods
├── Planning Worker Pods
├── Assistant Pods
├── Notification Workers
├── Evaluation Workers
└── Internal Services
```

### When to consider it

Only after ChronoMind genuinely has multiple independently scaling services or significant production traffic.

### Why not now?

Vercel + managed backend + managed PostgreSQL is far simpler and completely adequate for V2.

---

## 46.6 Multi-Agent Architecture

ChronoMind V2 intentionally uses **one primary LangGraph planning agent plus tools**.

Future versions may introduce specialized agents if planning complexity truly requires them.

Possible future agents:

```text
Planner Agent
Calendar Negotiation Agent
Long-Term Goal Agent
Study Strategy Agent
Reflection / Critic Agent
```

Possible supervisor design:

```text
                 Supervisor
                     │
        ┌────────────┼─────────────┐
        ▼            ▼             ▼
     Planner      Goal Agent    Calendar Agent
        │            │             │
        └────────────┴─────────────┘
                     │
                  Validator
```

### Purpose

Multi-agent systems can help when independent reasoning specialists need to collaborate on genuinely different problems.

### When to add

Add only when evaluations show that the single planning graph cannot reliably handle the required complexity.

### Why not now?

More agents mean:

```text
more LLM calls
more tokens
higher latency
more failure paths
harder debugging
harder evaluation
more complicated state coordination
```

The single-agent + tool architecture is stronger for V2.

---

## 46.7 Reinforcement Learning

Full reinforcement learning is a **future research direction**, not a V2 dependency.

### Possible purpose

ChronoMind could eventually learn scheduling policies based on long-term outcomes.

State:

```text
user context
current schedule
task categories
deadlines
behavior profile
```

Action:

```text
choose task ordering
choose time slot
choose whether to split
choose whether to suggest rescheduling
```

Reward might incorporate:

```text
task completion
deadline success
user acceptance
low reschedule count
low plan disruption
user satisfaction
```

Conceptually:

```text
State
  ↓
Policy
  ↓
Scheduling Action
  ↓
User Outcome
  ↓
Reward
  ↓
Policy Improvement
```

### Why not immediately?

Real RL requires:

```text
large amounts of interaction data
careful reward design
offline evaluation
safety constraints
exploration control
```

Poor reward design could teach undesirable planning behavior.

---

## 46.8 Contextual Bandits — Before Full RL

A contextual bandit is a more practical intermediate step.

### Purpose

Choose among several reasonable scheduling alternatives and learn which one the user tends to prefer.

Example:

```text
Context:
DSA task
Tuesday
user has 3 available windows

Choices:
7–8 AM
5–6 PM
8–9 PM

Observed result:
User repeatedly completes 8–9 PM sessions
```

The system gradually learns that preference.

This is simpler and safer than full RL because it optimizes immediate choices rather than long chains of actions.

---

## 46.9 Learning-to-Rank Model

As behavior data grows, replace part of the handcrafted priority formula with a learned ranking model.

Inputs:

```text
task category
deadline distance
user priority
goal relevance
time of day
day of week
reschedule count
historical completion rate
estimated duration
```

Output:

```text
relative task ranking
```

Possible models:

```text
LightGBM
XGBoost
small neural ranking model
```

### Purpose

Learn personalized priority ordering from real user behavior while keeping the scheduling constraints deterministic.

This can become one of the strongest ML components of ChronoMind.

---

## 46.10 Fine-Tuned Models

V2 should first use prompting, structured outputs, and model routing.

Fine-tuning becomes useful only when real application data shows repeated model errors.

Possible future fine-tuning targets:

```text
task intent classification
task-category classification
scheduling-command extraction
task decomposition
ChronoMind-specific response style
```

### Purpose

Improve:

```text
accuracy
latency
prompt size
domain consistency
cost
```

### Requirement

Never fine-tune merely to say that the project uses fine-tuning.

First create an evaluation dataset and prove that a fine-tuned model improves a measurable metric.

---

## 46.11 Local / On-Device Models

Future ChronoMind versions may route simple requests to a small local model.

Possible tasks:

```text
intent classification
task category prediction
basic natural-language parsing
short summaries
```

Architecture:

```text
User
 ↓
local/small model
 ↓
simple operation

complex request
 ↓
cloud reasoning model
```

### Purpose

Potential benefits:

```text
lower API cost
lower latency
better privacy
offline capability
```

---

## 46.12 Semantic Memory with pgvector

Structured facts should remain normal PostgreSQL data.

Examples:

```text
preferred working hours
task completion statistics
goal weights
deadlines
```

Semantic vector memory is useful for less structured information.

Examples:

```text
"I usually avoid studying after very long lab days."

"During placement months I want weekends mainly for mock interviews."

"I prefer coding tasks after dinner."
```

Pipeline:

```text
memory text
   ↓
embedding model
   ↓
pgvector
   ↓
semantic retrieval
   ↓
relevant memories only
   ↓
planner
```

### Purpose

Give the planning agent relevant long-term context without sending the user's entire history.

### Why pgvector?

It allows relational data and vector retrieval to live inside the same PostgreSQL stack.

A separate vector database should be introduced only if scale later justifies it.

---

## 46.13 ChronoMind Developer RAG Assistant

A developer-facing RAG bot can help understand and maintain the project.

Corpus:

```text
README.md
docs/architecture.md
docs/agent-workflow.md
docs/storage.md
docs/api.md
docs/evaluation.md
docs/deployment.md
```

Architecture:

```text
Developer question
      ↓
embedding
      ↓
documentation retrieval
      ↓
relevant sections
      ↓
LLM
      ↓
grounded answer
```

### Purpose

Examples:

```text
"Where is human approval implemented?"

"How does the priority engine work?"

"What database tables are involved in replanning?"

"Where should I add a new LangGraph node?"
```

This is separate from the end-user planning agent.

---

## 46.14 External Calendar Integration

Future integrations:

```text
Google Calendar
Microsoft Outlook Calendar
college timetable systems
```

Architecture:

```text
External calendar
      ↓
sync adapter
      ↓
normalized calendar events
      ↓
ChronoMind constraint engine
```

### Purpose

ChronoMind can understand real commitments automatically instead of requiring users to manually enter everything.

External events should normally be treated as fixed constraints unless the user explicitly allows modification.

---

## 46.15 Proactive Planning Agent

Core V2 reacts to explicit events and scheduled planning runs.

A later version may become more proactive.

Examples:

```text
deadline approaching
available focus block detected
important task repeatedly postponed
tomorrow overloaded
goal progress falling behind
unexpected free period appears
```

Then ChronoMind can generate a proposal:

```text
"You have a 90-minute free slot this evening.
Would you like me to move tomorrow's DSA practice here?"
```

The system should still respect notification limits and human control.

---

## 46.16 Multimodal Timetable and Document Understanding

Future ChronoMind may understand:

```text
class timetable images
exam schedules
assignment PDFs
syllabus documents
placement notices
```

Pipeline:

```text
Image / PDF
     ↓
OCR / multimodal model
     ↓
structured extraction
     ↓
validation
     ↓
user confirmation
     ↓
calendar / deadlines
```

### Purpose

Reduce manual task entry.

Extraction must never directly alter the calendar without validation and user confirmation.

---

## 46.17 Notification Intelligence

Instead of sending every notification immediately, a future notification model could determine:

```text
whether to notify
when to notify
how urgent
which channel
whether to bundle notifications
```

Inputs might include:

```text
deadline urgency
user activity
notification history
task importance
time of day
```

The aim is to reduce notification fatigue.

---

## 46.18 Experimentation / A-B Testing

As ChronoMind gains users, AI changes should be evaluated experimentally.

Examples:

```text
priority algorithm A vs B
different replanning policies
different explanation styles
different reminder timing
different task-splitting strategies
```

Measure:

```text
completion rate
acceptance rate
manual correction rate
deadline success
latency
cost
retention
```

This allows product decisions to be based on evidence.

---

## 46.19 Data Warehouse / Analytics Platform

PostgreSQL is sufficient for V2 analytics.

At large scale, operational data may be copied into an analytics warehouse.

Possible future purposes:

```text
large-scale behavioral analysis
product metrics
model training datasets
offline evaluation
experimentation
long-term trends
```

The warehouse must not become the live scheduling database.

---

## 46.20 Advanced Distributed Architecture

Only if ChronoMind reaches significant production scale:

```text
                    Clients
                       │
                       ▼
                  API Gateway
                       │
        ┌──────────────┼───────────────┐
        ▼              ▼               ▼
 Assistant API    Planning API     Task API
        │              │               │
        └──────────────┼───────────────┘
                       │
                     Kafka
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
 Behavior Worker   Notification    Analytics
        │            Worker          Pipeline
        │
      Redis
        │
 PostgreSQL / pgvector
        │
 LangGraph Workers
        │
 LLM Providers

Infrastructure:
Kubernetes / managed containers
distributed tracing
autoscaling
centralized observability
```

This is a **scale architecture**, not the architecture to build now.

---

# 47. Technology Evolution Map

The expected evolution is:

```text
CHRONOMIND V2 — BUILD NOW

React + TypeScript
FastAPI
PostgreSQL
Firebase Auth
LangGraph
Postgres Checkpoints
Priority Engine
Deterministic Scheduler
Validator
Replanning
Task Splitting
Human-in-the-loop
Behavior Events
Model Router
Structured LLM Tools
Evaluation
Observability


             ↓ real users + real measurements


CHRONOMIND V2.x — OPTIMIZE

Redis if needed
Background workers
pgvector semantic memory
OR-Tools
Learning-to-rank
Contextual bandits
External calendars
Multimodal timetable import
Better experimentation


             ↓ significant scale / complexity


CHRONOMIND V3+ — SCALE / RESEARCH

Specialized multi-agent workflows if justified
Fine-tuned domain models
Local/on-device models
Full reinforcement learning research
Kafka/event streaming
Microservices
Kubernetes
Data warehouse
Large-scale personalization infrastructure
```

---

# 48. Why These Technologies Are Deferred

| Technology | Purpose | Add when |
|---|---|---|
| Redis | Cache, locks, queue coordination | Multiple workers / high traffic |
| Job Queue | Durable asynchronous work | Planning jobs become long-running |
| Kafka | Event streaming | Many services need shared high-volume events |
| Microservices | Independent deployment/scaling | Modules need independent operation |
| Kubernetes | Container orchestration | Many services/workers need scaling |
| Multi-Agent AI | Specialized collaborative reasoning | Single planner demonstrably becomes insufficient |
| Contextual Bandits | Learn immediate user preferences | Enough interaction feedback exists |
| Full RL | Learn long-term policies | Large safe feedback dataset exists |
| Learning-to-Rank | Personalized task ordering | Enough behavior data exists |
| Fine-Tuning | Improve repeated domain-specific model tasks | Evaluation proves prompting is insufficient |
| pgvector | Semantic long-term memory/RAG | Structured memory no longer covers the use case |
| Local Models | Privacy, offline use, lower cost | Target devices/use case justify it |
| OR-Tools | Complex schedule optimization | Greedy scheduler stops meeting constraints |
| Data Warehouse | Large-scale analytics/training | Operational DB analytics become limiting |

This table is the rule for future architecture decisions.

---

# 49. What We Intentionally Do Not Add to Core V2

Core V2 does **not** initially require:

```text
many autonomous agents
full reinforcement learning
Kafka
microservices
Kubernetes
Redis
a separate vector database
LLM calls in every graph node
a huge model for simple commands
```

These are now explicitly documented as **future evolution options**, not missing parts of the project.

ChronoMind should earn additional complexity through measurable product requirements.

---

# 50. Example End-to-End Scenario

User says:

> "Placement season has started. I want DSA and aptitude to get more focus."

ChronoMind:

```text
voice/text input
     ↓
structured intent parser
     ↓
goal context updated
     ↓
priority engine recalculates affected tasks
     ↓
scheduler builds candidate week plan
     ↓
validator detects conflicts
     ↓
replanner creates alternative
     ↓
plan quality passes
     ↓
impact classified as high
     ↓
user sees proposed changes
     ↓
user accepts
     ↓
transaction writes schedule
     ↓
decision log saved
     ↓
future completion behavior is observed
```

Later the user misses a DSA session.

ChronoMind does not automatically move it to tomorrow.

It checks:

```text
deadline
goal relevance
reschedule count
tomorrow's load
available focus windows
splittability
behavior profile
```

It then proposes or applies the safest valid adjustment.

---

# 51. Definition of Done for ChronoMind V2

ChronoMind V2 is not complete merely because the LangGraph runs.

A usable V2 should satisfy:

```text
Task CRUD is timezone-safe.

Schedules cannot overlap.

Priority scores are deterministic and explainable.

Agent can create a valid candidate plan.

Invalid plans trigger bounded replanning.

High-impact changes pause for user approval.

Agent execution survives restart through checkpoints.

LLM output is schema-validated.

No regex action parsing remains.

User behavior is captured as events.

Behavior profile influences planning.

Agent decisions are auditable.

Token, latency, and cost metrics are visible.

An evaluation suite detects regressions.

Production scheduling does not depend on one FastAPI process.

Database writes are ownership-checked and transactional.

User can undo AI schedule changes.
```

---

# 52. Final Architecture Summary

```text
                           CHRONOMIND V2

                               USER
                                │
                    Manual / Text / Voice
                                │
                                ▼
                     React + TypeScript
                                │
                 Firebase Authentication
                                │
                                ▼
                            FastAPI
                                │
          ┌─────────────────────┼──────────────────────┐
          │                     │                      │
          ▼                     ▼                      ▼
      Task APIs           Assistant Layer       Planning API
                                │                      │
                                ▼                      ▼
                         Structured Tools      LangGraph Planner
                                                       │
                            ┌──────────────────────────┼───────────────┐
                            │                          │               │
                            ▼                          ▼               ▼
                     Priority Engine            Scheduler        Behavior
                            │                          │               │
                            └──────────────┬───────────┘               │
                                           ▼                           │
                                      Validator                        │
                                           │                           │
                                   invalid │ valid                     │
                                      ┌────┘                           │
                                      ▼                                │
                                   Replan                              │
                                      │                                │
                                      └──────────► Validator            │
                                           │                           │
                                           ▼                           │
                                  Human Approval?                      │
                                      │         │                      │
                                     no        yes                     │
                                      │         ▼                      │
                                      │      Interrupt                 │
                                      │         │                      │
                                      └────┬────┘                      │
                                           ▼                           │
                                        Execute                        │
                                           │                           │
                                           ▼                           │
                                    Decision Log                       │
                                           │                           │
                                           └────────► Outcome ─────────┘

                                  PostgreSQL
                                      │
              ┌───────────────────────┼────────────────────────┐
              │                       │                        │
           Tasks/Goals            Behavior               Agent State
                                                         Checkpoints

                                  AI Layer
                                      │
                       No LLM / Fast / Reasoning
                                      │
                               Model Router
```

---

# 53. Project Statement

> **ChronoMind V2 is an adaptive, stateful personal planning agent built with LangGraph, FastAPI, React, PostgreSQL, and LLM tool calling. It combines deterministic scheduling and optimization with selective LLM reasoning, durable memory, human-in-the-loop control, behavioral personalization, explainability, evaluation, observability, and cost-aware model routing to continuously produce feasible schedules aligned with a user's changing goals.**

---

# Repository

Current project:

https://github.com/shanmukhdatta/Chrono-Mind-AI

This README defines the target architecture for the ChronoMind V2 rebuild. Implementation should follow the phases above rather than attempting every component at once.
