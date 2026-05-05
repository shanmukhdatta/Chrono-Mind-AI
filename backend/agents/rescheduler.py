from typing import TypedDict, List, Dict, Optional
from langgraph.graph import StateGraph, END
from firebase_admin import firestore
from datetime import date, timedelta, datetime
from services.firebase_service import get_db
from services.notification_service import create_notification
import traceback
import copy

class AgentState(TypedDict):
    uid: str
    today: str
    tomorrow: str
    incomplete_tasks: List[Dict]
    not_important_task_ids: List[str]
    tomorrow_tasks: List[Dict]
    free_slots: List[tuple]
    rescheduled_tasks: List[Dict]
    deleted_count: int
    errors: List[str]

def add_minutes(time_str: str, minutes: int) -> str:
    h, m = map(int, time_str.split(':'))
    total = h * 60 + m + minutes
    new_h = (total // 60) % 24
    new_m = total % 60
    return f"{new_h:02d}:{new_m:02d}"

def time_diff_minutes(start: str, end: str) -> int:
    sh, sm = map(int, start.split(':'))
    eh, em = map(int, end.split(':'))
    return (eh * 60 + em) - (sh * 60 + sm)

def merge_adjacent_slots(slots: List[tuple]) -> List[tuple]:
    if not slots:
        return []
    sorted_slots = sorted(slots, key=lambda x: x[0])
    merged = [sorted_slots[0]]
    for current in sorted_slots[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def compute_free_slots_for_date(existing_tasks: List[Dict]) -> List[tuple]:
    """Compute free 08:00–22:00 slots for a given day's tasks"""
    occupied = sorted([(t['start_time'], t['end_time']) for t in existing_tasks])
    slots = []
    cursor = "08:00"
    while cursor < "22:00":
        slot_end = add_minutes(cursor, 15)
        overlap = any(s < slot_end and e > cursor for s, e in occupied)
        if not overlap:
            slots.append((cursor, slot_end))
        cursor = slot_end
    return merge_adjacent_slots(slots)

def fetch_incomplete(state: AgentState) -> AgentState:
    """Fetch incomplete tasks for today and split by importance"""
    try:
        db = get_db()
        tasks_ref = db.collection('users').document(state['uid']).collection('tasks')
        docs = tasks_ref.where('date', '==', state['today']).where('completed', '==', False).get()

        important = []
        not_important_ids = []

        for doc in docs:
            task = doc.to_dict()
            task['task_id'] = doc.id
            if task.get('importance') == 'important':
                important.append(task)
            else:
                not_important_ids.append(doc.id)

        state['incomplete_tasks'] = important
        state['not_important_task_ids'] = not_important_ids
    except Exception as e:
        state['errors'].append(f"fetch_incomplete error: {str(e)}")
    return state

def fetch_tomorrow(state: AgentState) -> AgentState:
    """Fetch existing tasks for tomorrow"""
    try:
        db = get_db()
        tasks_ref = db.collection('users').document(state['uid']).collection('tasks')
        docs = tasks_ref.where('date', '==', state['tomorrow']).get()

        tomorrow_tasks = []
        for doc in docs:
            task = doc.to_dict()
            task['task_id'] = doc.id
            tomorrow_tasks.append(task)

        state['tomorrow_tasks'] = tomorrow_tasks
    except Exception as e:
        state['errors'].append(f"fetch_tomorrow error: {str(e)}")
    return state

def compute_free_slots(state: AgentState) -> AgentState:
    """Compute free time slots for tomorrow between 08:00 and 22:00"""
    try:
        state['free_slots'] = compute_free_slots_for_date(state['tomorrow_tasks'])
    except Exception as e:
        state['errors'].append(f"compute_free_slots error: {str(e)}")
    return state

def assign_slots(state: AgentState) -> AgentState:
    """Assign incomplete tasks to free slots — greedy first-fit with 7-day lookahead"""
    try:
        rescheduled = []
        remaining_slots = list(state['free_slots'])

        for original_task in state['incomplete_tasks']:
            # Work on a copy to avoid mutation bugs on retry
            task = copy.deepcopy(original_task)
            needed = task.get('duration_minutes', 60)
            assigned = False

            # Try tomorrow first
            for i, (start, end) in enumerate(remaining_slots):
                slot_mins = time_diff_minutes(start, end)
                if slot_mins >= needed:
                    new_end = add_minutes(start, needed)
                    task['date'] = state['tomorrow']
                    task['start_time'] = start
                    task['end_time'] = new_end
                    task['rescheduled'] = True
                    task['rescheduled_from'] = state['today']
                    rescheduled.append(task)
                    # Trim slot
                    if new_end == end:
                        remaining_slots.pop(i)
                    else:
                        remaining_slots[i] = (new_end, end)
                    assigned = True
                    break

            if not assigned:
                # Try up to 7 days ahead
                for day_offset in range(2, 8):
                    future_date = (
                        datetime.strptime(state['tomorrow'], '%Y-%m-%d').date() +
                        timedelta(days=day_offset)
                    ).isoformat()

                    db = get_db()
                    future_docs = db.collection('users').document(state['uid'])\
                        .collection('tasks').where('date', '==', future_date).get()

                    future_tasks = [d.to_dict() for d in future_docs]
                    future_slots = compute_free_slots_for_date(future_tasks)

                    for fs, fe in future_slots:
                        if time_diff_minutes(fs, fe) >= needed:
                            task_copy = copy.deepcopy(task)
                            task_copy['date'] = future_date
                            task_copy['start_time'] = fs
                            task_copy['end_time'] = add_minutes(fs, needed)
                            task_copy['rescheduled'] = True
                            task_copy['rescheduled_from'] = state['today']
                            rescheduled.append(task_copy)
                            assigned = True
                            break

                    if assigned:
                        break

            if not assigned:
                state['errors'].append(f"Could not find slot for task: {task.get('title', 'unknown')}")

        state['rescheduled_tasks'] = rescheduled
    except Exception as e:
        state['errors'].append(f"assign_slots error: {str(e)}")
    return state

def write_rescheduled(state: AgentState) -> AgentState:
    """Write rescheduled tasks to Firestore"""
    try:
        db = get_db()
        for task in state['rescheduled_tasks']:
            task_ref = db.collection('users').document(state['uid'])\
                .collection('tasks').document(task['task_id'])
            task_ref.update({
                'date': task['date'],
                'start_time': task['start_time'],
                'end_time': task['end_time'],
                'rescheduled': True,
                'rescheduled_from': task['rescheduled_from'],
                'updated_at': firestore.SERVER_TIMESTAMP,
            })
    except Exception as e:
        state['errors'].append(f"write_rescheduled error: {str(e)}")
    return state

def delete_unimportant(state: AgentState) -> AgentState:
    """Delete not-important incomplete tasks"""
    deleted = 0
    try:
        db = get_db()
        for task_id in state['not_important_task_ids']:
            try:
                db.collection('users').document(state['uid'])\
                    .collection('tasks').document(task_id).delete()
                deleted += 1
            except Exception as e:
                state['errors'].append(f"delete error for {task_id}: {str(e)}")
    except Exception as e:
        state['errors'].append(f"delete_unimportant error: {str(e)}")
    state['deleted_count'] = deleted
    return state

def write_notification(state: AgentState) -> AgentState:
    """Create notifications for rescheduled and deleted tasks"""
    try:
        if state['rescheduled_tasks']:
            task_ids = [t['task_id'] for t in state['rescheduled_tasks']]
            count = len(task_ids)
            message = f"{count} important task{'s' if count > 1 else ''} from today were rescheduled."
            create_notification(state['uid'], 'tasks_rescheduled', message, task_ids)

        if state.get('deleted_count', 0) > 0:
            count = state['deleted_count']
            message = f"{count} low-priority incomplete task{'s' if count > 1 else ''} were cleared."
            create_notification(state['uid'], 'tasks_deleted', message, [])

    except Exception as e:
        state['errors'].append(f"write_notification error: {str(e)}")
    return state

def build_rescheduler_graph():
    g = StateGraph(AgentState)

    g.add_node('fetch_incomplete', fetch_incomplete)
    g.add_node('fetch_tomorrow', fetch_tomorrow)
    g.add_node('compute_free_slots', compute_free_slots)
    g.add_node('assign_slots', assign_slots)
    g.add_node('write_rescheduled', write_rescheduled)
    g.add_node('delete_unimportant', delete_unimportant)
    g.add_node('write_notification', write_notification)

    g.set_entry_point('fetch_incomplete')

    def route_from_fetch(state):
        if not state['incomplete_tasks']:
            return 'delete_unimportant'
        return 'fetch_tomorrow'

    g.add_conditional_edges('fetch_incomplete', route_from_fetch, {
        'fetch_tomorrow': 'fetch_tomorrow',
        'delete_unimportant': 'delete_unimportant'
    })

    g.add_edge('fetch_tomorrow', 'compute_free_slots')
    g.add_edge('compute_free_slots', 'assign_slots')
    g.add_edge('assign_slots', 'write_rescheduled')
    g.add_edge('write_rescheduled', 'delete_unimportant')
    g.add_edge('delete_unimportant', 'write_notification')
    g.add_edge('write_notification', END)

    return g.compile()

def run_for_user(uid: str, today: str, tomorrow: str):
    try:
        graph = build_rescheduler_graph()
        initial_state = {
            'uid': uid,
            'today': today,
            'tomorrow': tomorrow,
            'incomplete_tasks': [],
            'not_important_task_ids': [],
            'tomorrow_tasks': [],
            'free_slots': [],
            'rescheduled_tasks': [],
            'deleted_count': 0,
            'errors': []
        }
        result = graph.invoke(initial_state)
        if result['errors']:
            print(f"Agent warnings for {uid}: {result['errors']}")
        return result
    except Exception as e:
        print(f"Critical agent error for {uid}: {e}")
        traceback.print_exc()
        return None

def run_for_all_users():
    try:
        db = get_db()
        users = db.collection('users').get()
        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        print(f"Running rescheduling agent: {today} → {tomorrow}")
        for user_doc in users:
            try:
                result = run_for_user(user_doc.id, today, tomorrow)
                if result:
                    r = len(result.get('rescheduled_tasks', []))
                    d = result.get('deleted_count', 0)
                    print(f"  {user_doc.id}: rescheduled={r} deleted={d}")
            except Exception as e:
                print(f"Agent error for {user_doc.id}: {e}")
                traceback.print_exc()

        print("Rescheduling complete")
    except Exception as e:
        print(f"Critical error in run_for_all_users: {e}")
        traceback.print_exc()
