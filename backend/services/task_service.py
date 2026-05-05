from firebase_admin import firestore
from datetime import datetime, timedelta, date
from .firebase_service import get_db
from collections import defaultdict
import bleach

class ConflictError(Exception):
    pass

def sanitize_input(text):
    if not text:
        return ''
    return bleach.clean(text.strip(), tags=[], strip=True)

def check_time_conflict(uid, task_date, start_time, end_time, exclude_task_id=None):
    db = get_db()
    tasks_ref = db.collection('users').document(uid).collection('tasks')
    existing = tasks_ref.where('date', '==', task_date).get()

    for doc in existing:
        if exclude_task_id and doc.id == exclude_task_id:
            continue
        task = doc.to_dict()
        # Overlap: new_start < existing_end AND new_end > existing_start
        if start_time < task['end_time'] and end_time > task['start_time']:
            return task
    return None

def create_task(uid, data):
    db = get_db()

    conflict = check_time_conflict(uid, data.date, data.start_time, data.end_time)
    if conflict:
        raise ConflictError(f"Conflicts with '{conflict['title']}' ({conflict['start_time']} - {conflict['end_time']})")

    sh, sm = map(int, data.start_time.split(':'))
    eh, em = map(int, data.end_time.split(':'))
    duration = (eh * 60 + em) - (sh * 60 + sm)

    if duration < 15:
        raise ValueError('Task duration must be at least 15 minutes')

    task_data = {
        'uid': uid,
        'title': sanitize_input(data.title),
        'date': data.date,
        'start_time': data.start_time,
        'end_time': data.end_time,
        'duration_minutes': duration,
        'importance': data.importance,
        'recurrence': data.recurrence,
        'completed': False,
        'completed_at': None,
        'rescheduled': False,
        'rescheduled_from': None,
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
    }

    doc_ref = db.collection('users').document(uid).collection('tasks').document()
    doc_ref.set(task_data)
    task_data['task_id'] = doc_ref.id
    return task_data

def get_tasks(uid, date=None, status='all'):
    db = get_db()
    tasks_ref = db.collection('users').document(uid).collection('tasks')

    query = tasks_ref
    if date:
        query = query.where('date', '==', date)

    query = query.order_by('start_time')
    docs = query.get()
    tasks = []

    for doc in docs:
        task = doc.to_dict()
        task['task_id'] = doc.id

        # Serialize Firestore timestamps
        for field in ('created_at', 'updated_at', 'completed_at'):
            if task.get(field) and hasattr(task[field], 'isoformat'):
                task[field] = task[field].isoformat()
            elif task.get(field) and hasattr(task[field], 'timestamp'):
                task[field] = datetime.fromtimestamp(task[field].timestamp()).isoformat()

        if status == 'completed' and not task.get('completed'):
            continue
        if status == 'incomplete' and task.get('completed'):
            continue

        tasks.append(task)

    return tasks

def update_task(uid, task_id, updates):
    db = get_db()
    task_ref = db.collection('users').document(uid).collection('tasks').document(task_id)
    doc = task_ref.get()

    if not doc.exists:
        raise ValueError('Task not found')

    current = doc.to_dict()
    if current.get('uid') != uid:
        raise ValueError('Unauthorized')

    update_data = {}

    if updates.title is not None:
        update_data['title'] = sanitize_input(updates.title)
    if updates.date is not None:
        update_data['date'] = updates.date
    if updates.start_time is not None:
        update_data['start_time'] = updates.start_time
    if updates.end_time is not None:
        update_data['end_time'] = updates.end_time
    if updates.importance is not None:
        update_data['importance'] = updates.importance
    if updates.recurrence is not None:
        update_data['recurrence'] = updates.recurrence

    if 'start_time' in update_data or 'end_time' in update_data:
        start = update_data.get('start_time', current['start_time'])
        end = update_data.get('end_time', current['end_time'])

        conflict = check_time_conflict(
            uid,
            update_data.get('date', current['date']),
            start, end,
            exclude_task_id=task_id
        )
        if conflict:
            raise ConflictError(f"Conflicts with '{conflict['title']}' ({conflict['start_time']} - {conflict['end_time']})")

        sh, sm = map(int, start.split(':'))
        eh, em = map(int, end.split(':'))
        update_data['duration_minutes'] = (eh * 60 + em) - (sh * 60 + sm)

    update_data['updated_at'] = firestore.SERVER_TIMESTAMP
    task_ref.update(update_data)

    updated = task_ref.get().to_dict()
    updated['task_id'] = task_id
    # Serialize timestamps
    for field in ('created_at', 'updated_at', 'completed_at'):
        if updated.get(field) and hasattr(updated[field], 'isoformat'):
            updated[field] = updated[field].isoformat()
        elif updated.get(field) and hasattr(updated[field], 'timestamp'):
            updated[field] = datetime.fromtimestamp(updated[field].timestamp()).isoformat()
    return updated

def delete_task(uid, task_id):
    db = get_db()
    task_ref = db.collection('users').document(uid).collection('tasks').document(task_id)
    doc = task_ref.get()

    if not doc.exists:
        raise ValueError('Task not found')
    if doc.to_dict().get('uid') != uid:
        raise ValueError('Unauthorized')

    task_ref.delete()
    return True

def complete_task(uid, task_id):
    db = get_db()
    task_ref = db.collection('users').document(uid).collection('tasks').document(task_id)
    doc = task_ref.get()

    if not doc.exists:
        raise ValueError('Task not found')

    task_ref.update({
        'completed': True,
        'completed_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
    })

    updated = task_ref.get().to_dict()
    updated['task_id'] = task_id
    return updated

def get_stats(uid):
    """Get stats with a single Firestore read — no N+1 query"""
    db = get_db()
    tasks_ref = db.collection('users').document(uid).collection('tasks')
    docs = tasks_ref.get()

    total = 0
    completed = 0
    rescheduled = 0
    dates_with_completions = set()

    for doc in docs:
        total += 1
        task = doc.to_dict()
        if task.get('completed'):
            completed += 1
            if task.get('date'):
                dates_with_completions.add(task['date'])
        if task.get('rescheduled'):
            rescheduled += 1

    # Calculate streak from pre-built set — O(365) dict lookups, 0 extra Firestore reads
    streak = 0
    today = date.today()
    for i in range(365):
        check_date = (today - timedelta(days=i)).isoformat()
        if check_date in dates_with_completions:
            streak += 1
        else:
            break

    return {
        'total_created': total,
        'completed': completed,
        'rescheduled': rescheduled,
        'current_streak': streak,
        'completion_rate': round((completed / total * 100) if total > 0 else 0, 1)
    }

def generate_recurring_instances(uid, task, from_date_str, days=30):
    """Generate future instances of a recurring task"""
    db = get_db()
    recurrence = task.get('recurrence', 'none')
    if recurrence == 'none':
        return

    from_date = date.fromisoformat(from_date_str)
    task_date = date.fromisoformat(task['date'])
    
    # Map recurrence to weekdays
    day_map = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
    
    instances_created = 0
    for i in range(1, days + 1):
        target = from_date + timedelta(days=i)
        should_create = False

        if recurrence == 'daily':
            should_create = True
        elif recurrence == 'weekly':
            should_create = (target.weekday() == task_date.weekday())
        else:
            # Custom: "mon,wed,fri"
            target_days = [d.strip() for d in recurrence.split(',')]
            target_day_nums = [day_map.get(d.lower()) for d in target_days if d.lower() in day_map]
            should_create = (target.weekday() in target_day_nums)

        if should_create:
            # Check if instance already exists
            existing = db.collection('users').document(uid).collection('tasks')\
                .where('date', '==', target.isoformat())\
                .where('start_time', '==', task['start_time'])\
                .where('title', '==', task['title'])\
                .get()
            
            if not existing:
                new_task = {
                    'uid': uid,
                    'title': task['title'],
                    'date': target.isoformat(),
                    'start_time': task['start_time'],
                    'end_time': task['end_time'],
                    'duration_minutes': task.get('duration_minutes', 60),
                    'importance': task.get('importance', 'important'),
                    'recurrence': recurrence,
                    'recurrence_parent_id': task.get('task_id', ''),
                    'completed': False,
                    'completed_at': None,
                    'rescheduled': False,
                    'rescheduled_from': None,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'updated_at': firestore.SERVER_TIMESTAMP,
                }
                db.collection('users').document(uid).collection('tasks').document().set(new_task)
                instances_created += 1

    return instances_created

def get_tasks_range(uid, date_from, date_to, status='all'):
    """Fetch tasks between two dates — used by CalendarMonth"""
    db = get_db()
    tasks_ref = db.collection('users').document(uid).collection('tasks')
    docs = tasks_ref \
        .where('date', '>=', date_from) \
        .where('date', '<=', date_to) \
        .order_by('date') \
        .order_by('start_time') \
        .get()

    tasks = []
    for doc in docs:
        task = doc.to_dict()
        task['task_id'] = doc.id
        for field in ('created_at', 'updated_at', 'completed_at'):
            if task.get(field) and hasattr(task[field], 'isoformat'):
                task[field] = task[field].isoformat()
            elif task.get(field) and hasattr(task[field], 'timestamp'):
                task[field] = datetime.fromtimestamp(task[field].timestamp()).isoformat()
        if status == 'completed' and not task.get('completed'):
            continue
        if status == 'incomplete' and task.get('completed'):
            continue
        tasks.append(task)
    return tasks
