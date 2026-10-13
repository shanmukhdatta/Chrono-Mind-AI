"""Legacy nightly rollover graph; non-destructive and overlap-aware.

V2 will replace direct writes with user-approved proposals and transactions.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, TypedDict
from zoneinfo import ZoneInfo

from firebase_admin import firestore
from langgraph.graph import END, StateGraph

from agents.missed_task_policy import select_rollover_candidates
from agents.slot_planner import free_intervals, plan_rollover, to_clock
from services.firebase_service import get_db
from services.notification_service import create_notification

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")


class AgentState(TypedDict):
    uid: str
    today: str
    tomorrow: str
    incomplete_tasks: List[Dict]
    tomorrow_tasks: List[Dict]
    free_slots: List[tuple]
    rescheduled_tasks: List[Dict]
    errors: List[str]


def compute_free_slots_for_date(existing_tasks: List[Dict]) -> List[tuple]:
    """Compatibility helper for callers expecting HH:MM slot pairs."""
    return [(to_clock(s), to_clock(e)) for s, e in free_intervals(existing_tasks)]


def fetch_incomplete(state: AgentState) -> AgentState:
    try:
        tasks_ref = get_db().collection("users").document(state["uid"]).collection("tasks")
        docs = tasks_ref.where("date", "==", state["today"]).where("completed", "==", False).get()
        candidates = []
        for doc in docs:
            task = doc.to_dict()
            task["task_id"] = doc.id
            candidates.append(task)
        state["incomplete_tasks"] = select_rollover_candidates(candidates)
    except Exception as exc:
        logger.exception("Failed to fetch missed tasks")
        state["errors"].append(f"fetch_incomplete failed: {type(exc).__name__}")
    return state


def fetch_tomorrow(state: AgentState) -> AgentState:
    if state["errors"]:
        return state
    try:
        tasks_ref = get_db().collection("users").document(state["uid"]).collection("tasks")
        docs = tasks_ref.where("date", "==", state["tomorrow"]).get()
        state["tomorrow_tasks"] = [doc.to_dict() for doc in docs]
    except Exception as exc:
        logger.exception("Failed to fetch next-day tasks")
        state["errors"].append(f"fetch_tomorrow failed: {type(exc).__name__}")
    return state


def compute_free_slots(state: AgentState) -> AgentState:
    if state["errors"]:
        return state
    try:
        state["free_slots"] = compute_free_slots_for_date(state["tomorrow_tasks"])
    except Exception as exc:
        state["errors"].append(f"compute_free_slots failed: {type(exc).__name__}")
    return state


def assign_slots(state: AgentState) -> AgentState:
    if state["errors"]:
        return state
    try:
        tasks_ref = get_db().collection("users").document(state["uid"]).collection("tasks")

        def load_existing(day: str):
            if day == state["tomorrow"]:
                return state["tomorrow_tasks"]
            return [doc.to_dict() for doc in tasks_ref.where("date", "==", day).get()]

        placements, unplaced = plan_rollover(
            state["incomplete_tasks"], state["tomorrow"], load_existing, horizon_days=7
        )
        state["rescheduled_tasks"] = placements
        for task_id in unplaced:
            state["errors"].append(f"No free slot for task {task_id}")
    except Exception as exc:
        logger.exception("Slot assignment failed")
        state["rescheduled_tasks"] = []
        state["errors"].append(f"assign_slots failed: {type(exc).__name__}")
    return state


def write_rescheduled(state: AgentState) -> AgentState:
    """Best-effort legacy writes with read-before-write conflict protection.

    These are not yet atomic against interactive edits; Phase 5/7 must replace
    them with versioned transactional acceptance.
    """
    if any("failed:" in err for err in state["errors"]):
        state["rescheduled_tasks"] = []
        return state
    committed = []
    try:
        tasks_ref = get_db().collection("users").document(state["uid"]).collection("tasks")
        for task in state["rescheduled_tasks"]:
            try:
                ref = tasks_ref.document(task["task_id"])
                source = ref.get()
                if not source.exists:
                    state["errors"].append(f"Task vanished: {task['task_id']}")
                    continue
                current = source.to_dict()
                if current.get("date") != state["today"] or current.get("completed"):
                    state["errors"].append(f"Task changed since selection: {task['task_id']}")
                    continue
                if current.get("importance") != "important":
                    continue
                current_day = tasks_ref.where("date", "==", task["date"]).get()
                overlapping = False
                for doc in current_day:
                    if doc.id == task["task_id"]:
                        continue
                    other = doc.to_dict()
                    if (task["start_time"] < other["end_time"]
                            and task["end_time"] > other["start_time"]):
                        overlapping = True
                        break
                if overlapping:
                    state["errors"].append(f"Slot occupied during write: {task['task_id']}")
                    continue
                ref.update({
                    "date": task["date"],
                    "start_time": task["start_time"],
                    "end_time": task["end_time"],
                    "rescheduled": True,
                    "rescheduled_from": state["today"],
                    "updated_at": firestore.SERVER_TIMESTAMP,
                })
                committed.append(task)
            except Exception as exc:
                logger.exception("Could not move task %s", task.get("task_id"))
                state["errors"].append(
                    f"Write failed for {task.get('task_id')}: {type(exc).__name__}"
                )
    except Exception as exc:
        logger.exception("Unable to access tasks for rollover")
        state["errors"].append(f"write_rescheduled failed: {type(exc).__name__}")
    state["rescheduled_tasks"] = committed
    return state


def write_notification(state: AgentState) -> AgentState:
    if state["rescheduled_tasks"]:
        try:
            task_ids = [task["task_id"] for task in state["rescheduled_tasks"]]
            count = len(task_ids)
            create_notification(
                state["uid"], "tasks_rescheduled",
                f"{count} important task{'s' if count != 1 else ''} was/were rescheduled.",
                task_ids,
            )
        except Exception as exc:
            logger.exception("Notification write failed")
            state["errors"].append(f"write_notification failed: {type(exc).__name__}")
    return state


def build_rescheduler_graph():
    graph = StateGraph(AgentState)
    for name, callback in (
        ("fetch_incomplete", fetch_incomplete),
        ("fetch_tomorrow", fetch_tomorrow),
        ("compute_free_slots", compute_free_slots),
        ("assign_slots", assign_slots),
        ("write_rescheduled", write_rescheduled),
        ("write_notification", write_notification),
    ):
        graph.add_node(name, callback)
    graph.set_entry_point("fetch_incomplete")
    graph.add_conditional_edges(
        "fetch_incomplete",
        lambda state: "fetch_tomorrow" if state["incomplete_tasks"] and not state["errors"] else "write_notification",
        {"fetch_tomorrow": "fetch_tomorrow", "write_notification": "write_notification"},
    )
    graph.add_edge("fetch_tomorrow", "compute_free_slots")
    graph.add_edge("compute_free_slots", "assign_slots")
    graph.add_edge("assign_slots", "write_rescheduled")
    graph.add_edge("write_rescheduled", "write_notification")
    graph.add_edge("write_notification", END)
    return graph.compile()


def run_for_user(uid: str, today: str, tomorrow: str):
    initial_state: AgentState = {
        "uid": uid,
        "today": today,
        "tomorrow": tomorrow,
        "incomplete_tasks": [],
        "tomorrow_tasks": [],
        "free_slots": [],
        "rescheduled_tasks": [],
        "errors": [],
    }
    try:
        result = build_rescheduler_graph().invoke(initial_state)
        if result["errors"]:
            logger.warning("Rollover issues for %s: %s", uid, result["errors"])
        return result
    except Exception:
        logger.exception("Rescheduling graph failed for %s", uid)
        return None


def run_for_all_users():
    """Execute once for each user; caller is responsible for distributed locking."""
    local_today = datetime.now(IST).date()
    today = local_today.isoformat()
    tomorrow = (local_today + timedelta(days=1)).isoformat()
    users = get_db().collection("users").get()
    processed = moved = errors = 0
    for user_doc in users:
        processed += 1
        result = run_for_user(user_doc.id, today, tomorrow)
        if result is None:
            errors += 1
        else:
            moved += len(result["rescheduled_tasks"])
            errors += len(result["errors"])
    logger.info("Nightly rollover completed: users=%d moved=%d issues=%d", processed, moved, errors)
    return {"users": processed, "moved": moved, "errors": errors}
