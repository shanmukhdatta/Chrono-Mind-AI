"""
ChronoMind AI — LangGraph Agentic Scheduler
Multi-step reasoning agent for intelligent task scheduling
"""
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.models import Task, TaskCategory, TaskStatus, User
from app.models.schemas import TaskOut
from app.services.scheduler_service import (
    find_free_slots, find_best_slot, get_busy_slots,
    has_conflict, time_to_minutes, minutes_to_time
)

logger = logging.getLogger(__name__)


# ─── Agent State ──────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    user_name: str
    user_prefs: Dict[str, Any]
    db: Any  # AsyncSession (can't type properly in TypedDict)
    created_tasks: List[Dict]
    updated_tasks: List[Dict]
    found_slots: List[Dict]
    action_type: str


# ─── System Prompt ────────────────────────────────────────────────

def build_system_prompt(user_name: str, user_prefs: Dict, today: str) -> str:
    return f"""You are ChronoMind AI — the intelligent scheduling assistant for {user_name}.

Today is {today} ({date.today().strftime('%A')}).

Your personality:
- Warm, encouraging, and proactive
- Concise but complete — never over-explain
- Always confirm what you've done
- Use emojis sparingly but effectively (✅ for success, 📅 for calendar, ⚡ for quick actions)

User preferences:
- Chronotype: {user_prefs.get('chronotype', 'flexible')}
- Break style: {user_prefs.get('break_style', 'pomodoro')}
- Preferred hours: {user_prefs.get('preferred_start_hour', 8)}:00 — {user_prefs.get('preferred_end_hour', 22)}:00
- Default study duration: {user_prefs.get('default_study_duration', 90)} minutes

You have access to these tools:
1. `schedule_task` — Schedule a new task into the best available slot
2. `find_slots` — Show available time slots for a given date
3. `list_todays_tasks` — Get today's schedule
4. `complete_task` — Mark a task as complete
5. `reschedule_task` — Move a task to a new time slot

When scheduling:
- Always find the best free slot automatically
- Respect class schedule conflicts
- Consider the user's chronotype for optimal placement
- If no slot today, suggest tomorrow with explanation
- Confirm the final schedule clearly

Keep responses under 150 words unless listing multiple tasks."""


# ─── LLM + Tools ──────────────────────────────────────────────────

def get_llm():
    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your .env file. "
            "Get a free key at https://console.groq.com"
        )
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=1024,
    )


# ─── Agent Nodes ──────────────────────────────────────────────────

async def parse_intent_node(state: AgentState) -> AgentState:
    """Parse user intent and extract scheduling parameters."""
    db: AsyncSession = state["db"]
    messages = state["messages"]
    user_prefs = state["user_prefs"]

    today = date.today().isoformat()
    system = build_system_prompt(state["user_name"], user_prefs, today)

    # Add context about today's schedule
    try:
        busy = await get_busy_slots(db, state["user_id"], date.today())
        schedule_context = f"\n\nToday's busy slots: {json.dumps(busy[:5])}"
        system += schedule_context
    except Exception:
        pass

    llm = get_llm()
    llm_with_tools = llm.bind_tools([
        schedule_task_tool,
        find_slots_tool,
        list_tasks_tool,
        complete_task_tool,
    ])

    all_messages = [SystemMessage(content=system)] + messages
    response = await llm_with_tools.ainvoke(all_messages)

    return {**state, "messages": [response]}


async def execute_tools_node(state: AgentState) -> AgentState:
    """Execute any tool calls made by the LLM."""
    last_message = state["messages"][-1]
    db: AsyncSession = state["db"]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return state

    tool_results = []
    created_tasks = list(state.get("created_tasks", []))
    found_slots = list(state.get("found_slots", []))
    action_type = state.get("action_type", "chat")

    for tool_call in last_message.tool_calls:
        name = tool_call["name"]
        args = tool_call["args"]
        result = {}

        try:
            if name == "schedule_task":
                result = await _execute_schedule_task(db, state["user_id"], state["user_prefs"], args)
                if result.get("success"):
                    created_tasks.append(result.get("task", {}))
                    action_type = "schedule"

            elif name == "find_slots":
                result = await _execute_find_slots(db, state["user_id"], state["user_prefs"], args)
                found_slots.extend(result.get("slots", []))
                action_type = "query"

            elif name == "list_tasks":
                result = await _execute_list_tasks(db, state["user_id"], args)
                action_type = "query"

            elif name == "complete_task":
                result = await _execute_complete_task(db, state["user_id"], args)
                action_type = "update"

        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            result = {"error": str(e), "success": False}

        from langchain_core.messages import ToolMessage
        tool_results.append(
            ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"])
        )

    return {
        **state,
        "messages": tool_results,
        "created_tasks": created_tasks,
        "found_slots": found_slots,
        "action_type": action_type,
    }


async def synthesize_response_node(state: AgentState) -> AgentState:
    """Generate the final conversational response after tool execution."""
    messages = state["messages"]
    user_prefs = state["user_prefs"]

    # Check if there are tool results that need a final response
    has_tool_messages = any(
        hasattr(m, "type") and m.type == "tool" for m in messages
    )
    if not has_tool_messages:
        return state

    llm = get_llm()
    today = date.today().isoformat()
    system = build_system_prompt(state["user_name"], user_prefs, today)
    system += "\n\nBased on the tool results, give a friendly, concise confirmation of what was done."

    all_messages = [SystemMessage(content=system)] + messages
    response = await llm.ainvoke(all_messages)

    return {**state, "messages": [response]}


def should_execute_tools(state: AgentState) -> str:
    """Router: go to tool execution or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "execute_tools"
    return "end"


def after_tools(state: AgentState) -> str:
    """After tool execution, synthesize response."""
    return "synthesize"


# ─── Tool Implementations ─────────────────────────────────────────

@tool
def schedule_task_tool(
    title: str,
    duration_minutes: int = 60,
    category: str = "study",
    deadline_days: Optional[int] = None,
    description: str = "",
) -> dict:
    """Schedule a new task into the best available free slot on the calendar."""
    return {"status": "pending", "title": title, "duration_minutes": duration_minutes}


@tool
def find_slots_tool(date_offset: int = 0, duration_minutes: int = 60) -> dict:
    """Find available free time slots. date_offset: 0=today, 1=tomorrow, etc."""
    return {"status": "pending", "date_offset": date_offset, "duration_minutes": duration_minutes}


@tool
def list_tasks_tool(date_offset: int = 0) -> dict:
    """List all scheduled tasks for a given day. date_offset: 0=today, 1=tomorrow."""
    return {"status": "pending", "date_offset": date_offset}


@tool
def complete_task_tool(task_title: str) -> dict:
    """Mark a task as completed by its title (fuzzy match)."""
    return {"status": "pending", "task_title": task_title}


# Rename for binding
schedule_task_tool.name = "schedule_task"
find_slots_tool.name = "find_slots"
list_tasks_tool.name = "list_tasks"
complete_task_tool.name = "complete_task"


async def _execute_schedule_task(
    db: AsyncSession, user_id: str, prefs: Dict, args: Dict
) -> Dict:
    """Actually schedule a task in the database."""
    from sqlalchemy import select

    title = args.get("title", "New Task")
    duration = int(args.get("duration_minutes", 60))
    category = args.get("category", "study")
    deadline_days = args.get("deadline_days")
    description = args.get("description", "")

    deadline = None
    if deadline_days is not None:
        deadline = datetime.now() + timedelta(days=int(deadline_days))

    # Find best slot
    slot = await find_best_slot(
        db=db,
        user_id=user_id,
        duration_minutes=duration,
        deadline=deadline,
        preferred_start=prefs.get("preferred_start_hour", 8) * 60,
        preferred_end=prefs.get("preferred_end_hour", 22) * 60,
        chronotype=prefs.get("chronotype", "flexible"),
    )

    if not slot:
        return {
            "success": False,
            "message": "No free slot found in the next 7 days that fits this task.",
        }

    slot_date, start_time, end_time = slot

    # Map category
    cat_map = {
        "study": TaskCategory.STUDY,
        "assignment": TaskCategory.ASSIGNMENT,
        "project": TaskCategory.PROJECT,
        "personal": TaskCategory.PERSONAL,
        "exercise": TaskCategory.EXERCISE,
    }
    task_category = cat_map.get(category.lower(), TaskCategory.STUDY)

    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        category=task_category,
        duration_minutes=duration,
        deadline=deadline,
        scheduled_date=slot_date.isoformat(),
        start_time=start_time,
        end_time=end_time,
        ai_placed=True,
        ai_reasoning=f"Best free slot found: {slot_date.strftime('%A, %b %d')} {start_time}–{end_time}",
        priority_score=0.8 if deadline_days and deadline_days <= 2 else 0.5,
    )

    db.add(task)
    await db.flush()
    await db.refresh(task)

    return {
        "success": True,
        "message": f"Scheduled '{title}' on {slot_date.strftime('%A, %B %d')} from {start_time} to {end_time}.",
        "task": {
            "id": task.id,
            "title": task.title,
            "scheduled_date": task.scheduled_date,
            "start_time": task.start_time,
            "end_time": task.end_time,
            "duration_minutes": task.duration_minutes,
            "category": task.category.value,
        },
    }


async def _execute_find_slots(
    db: AsyncSession, user_id: str, prefs: Dict, args: Dict
) -> Dict:
    target_date = date.today() + timedelta(days=int(args.get("date_offset", 0)))
    duration = int(args.get("duration_minutes", 60))

    slots = await find_free_slots(
        db, user_id, target_date, duration,
        prefs.get("preferred_start_hour", 8) * 60,
        prefs.get("preferred_end_hour", 22) * 60,
    )

    return {
        "date": target_date.isoformat(),
        "day": target_date.strftime("%A"),
        "slots": slots[:5],  # Top 5
        "count": len(slots),
    }


async def _execute_list_tasks(db: AsyncSession, user_id: str, args: Dict) -> Dict:
    from sqlalchemy import select, and_
    target_date = date.today() + timedelta(days=int(args.get("date_offset", 0)))
    date_str = target_date.isoformat()

    result = await db.execute(
        select(Task).where(and_(Task.user_id == user_id, Task.scheduled_date == date_str))
    )
    tasks = result.scalars().all()

    return {
        "date": date_str,
        "day": target_date.strftime("%A"),
        "tasks": [
            {
                "title": t.title,
                "start_time": t.start_time,
                "end_time": t.end_time,
                "status": t.status.value,
                "category": t.category.value,
            }
            for t in tasks
        ],
        "count": len(tasks),
    }


async def _execute_complete_task(db: AsyncSession, user_id: str, args: Dict) -> Dict:
    from sqlalchemy import select, and_
    title = args.get("task_title", "")

    result = await db.execute(
        select(Task).where(
            and_(
                Task.user_id == user_id,
                Task.title.ilike(f"%{title}%"),
                Task.status == TaskStatus.PENDING,
            )
        )
    )
    task = result.scalars().first()

    if not task:
        return {"success": False, "message": f"No pending task matching '{title}' found."}

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now()
    await db.flush()

    return {"success": True, "message": f"Marked '{task.title}' as completed! ✅"}


# ─── Build Graph ──────────────────────────────────────────────────

def build_agent_graph() -> StateGraph:
    """Build and compile the LangGraph agent."""
    graph = StateGraph(AgentState)

    graph.add_node("parse_intent", parse_intent_node)
    graph.add_node("execute_tools", execute_tools_node)
    graph.add_node("synthesize", synthesize_response_node)

    graph.set_entry_point("parse_intent")

    graph.add_conditional_edges(
        "parse_intent",
        should_execute_tools,
        {"execute_tools": "execute_tools", "end": END},
    )

    graph.add_edge("execute_tools", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


# Singleton compiled graph
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        try:
            _agent = build_agent_graph()
        except Exception as e:
            logger.error(f"Failed to build agent graph: {e}")
            raise
    return _agent


# ─── Main Entry Point ─────────────────────────────────────────────

async def run_agent(
    db: AsyncSession,
    user: User,
    user_message: str,
    history: List[Dict],
) -> Dict:
    """
    Run the ChronoMind scheduling agent.
    Returns: {message, tasks_created, tasks_updated, slots_found, action_type}
    """
    # Guard: friendly message if no API key
    if not settings.GROQ_API_KEY:
        return {
            "message": (
                "⚠️ AI features require a Groq API key. "
                "Add GROQ_API_KEY to your backend/.env file. "
                "Get a free key at https://console.groq.com/keys"
            ),
            "tasks_created": [],
            "tasks_updated": [],
            "slots_found": [],
            "action_type": "error",
        }
    agent = get_agent()

    # Build message history
    messages = []
    for msg in history[-6:]:  # Last 6 messages for context
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_message))

    user_prefs = {
        "chronotype": user.chronotype.value if user.chronotype else "flexible",
        "break_style": user.break_style or "pomodoro",
        "default_study_duration": user.default_study_duration or 90,
        "preferred_start_hour": user.preferred_start_hour or 8,
        "preferred_end_hour": user.preferred_end_hour or 22,
    }

    initial_state: AgentState = {
        "messages": messages,
        "user_id": user.id,
        "user_name": user.name,
        "user_prefs": user_prefs,
        "db": db,
        "created_tasks": [],
        "updated_tasks": [],
        "found_slots": [],
        "action_type": "chat",
    }

    try:
        final_state = await agent.ainvoke(initial_state)

        # Extract final AI message
        ai_messages = [
            m for m in final_state["messages"]
            if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None)
        ]
        response_text = ai_messages[-1].content if ai_messages else "I processed your request."

        return {
            "message": response_text,
            "tasks_created": final_state.get("created_tasks", []),
            "tasks_updated": final_state.get("updated_tasks", []),
            "slots_found": final_state.get("found_slots", []),
            "action_type": final_state.get("action_type", "chat"),
        }

    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        # Fallback to simple LLM response
        llm = get_llm()
        fallback = await llm.ainvoke([
            SystemMessage(content=f"You are ChronoMind AI, a helpful scheduling assistant for {user.name}. Today is {date.today()}."),
            HumanMessage(content=user_message),
        ])
        return {
            "message": fallback.content,
            "tasks_created": [],
            "tasks_updated": [],
            "slots_found": [],
            "action_type": "chat",
        }
