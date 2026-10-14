"""Authenticated PostgreSQL V2 APIs; legacy Firestore routes stay unchanged."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_or_create_user, get_session
from .models import Goal, Task, Preference, User, ScheduleBlock, TaskDependency, RecurrenceOccurrence, FocusSession, InAppNotification
from .schemas import GoalCreate, GoalOut, GoalUpdate, TaskCreate, TaskOut, TaskUpdate, PreferencesOut, PreferencesUpdate

router = APIRouter(prefix="/api/v2", tags=["v2"])


def _owned(session: Session, model, uid: str, item_id: str):
    row = session.scalar(select(model).where(model.id == item_id, model.owner_uid == uid))
    if row is None:
        raise HTTPException(404, "Not found")
    return row


def _check_goal(session: Session, uid: str, goal_id: str | None):
    if goal_id is not None:
        _owned(session, Goal, uid, goal_id)


@router.get("/goals", response_model=list[GoalOut])
def list_goals(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    return db.scalars(select(Goal).where(Goal.owner_uid == user["uid"]).order_by(Goal.created_at)).all()


@router.post("/goals", response_model=GoalOut, status_code=201)
def create_goal(body: GoalCreate, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    get_or_create_user(db, uid)
    row = Goal(owner_uid=uid, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/goals/{goal_id}", response_model=GoalOut)
def patch_goal(goal_id: str, body: GoalUpdate, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    row = _owned(db, Goal, user["uid"], goal_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        if key in ("title", "description", "status") and value is None:
            raise HTTPException(422, key + " cannot be null")
        if key == "title" and not value.strip():
            raise HTTPException(422, "Title cannot be blank")
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/goals/{goal_id}", status_code=204)
def delete_goal(goal_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    row = _owned(db, Goal, uid, goal_id)
    db.execute(update(Task).where(Task.owner_uid == uid, Task.goal_id == goal_id).values(goal_id=None))
    db.delete(row)
    db.commit()


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(status: str = "all", user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    if status not in ("all", "pending", "completed", "archived"):
        raise HTTPException(422, "Invalid task status")
    query = select(Task).where(Task.owner_uid == user["uid"])
    if status != "all":
        query = query.where(Task.status == status)
    return db.scalars(query.order_by(Task.created_at, Task.id)).all()


@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(body: TaskCreate, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    get_or_create_user(db, uid)
    _check_goal(db, uid, body.goal_id)
    row = Task(owner_uid=uid, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    return _owned(db, Task, user["uid"], task_id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def patch_task(task_id: str, body: TaskUpdate, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    # All V2 calendar/task writes acquire the same owner-row lock first.
    db.scalar(select(User).where(User.uid == uid).with_for_update())
    changes = body.model_dump(exclude_unset=True, exclude={"version"})
    for key in ("title", "description", "duration_minutes", "importance", "status"):
        if key in changes and changes[key] is None:
            raise HTTPException(422, key + " cannot be null")
    if "title" in changes and not changes["title"].strip():
        raise HTTPException(422, "Title cannot be blank")
    if "goal_id" in changes:
        _check_goal(db, uid, changes["goal_id"])
    original = _owned(db, Task, uid, task_id)
    now = datetime.now(timezone.utc)
    scheduled = db.scalars(select(ScheduleBlock).where(
        ScheduleBlock.owner_uid == uid, ScheduleBlock.task_id == task_id
    )).all()
    # Never accept an effort/deadline edit that invalidates already booked work.
    booked_minutes = sum(
        int((end_aware(b.ends_at) - end_aware(b.starts_at)).total_seconds() // 60)
        for b in scheduled
    )
    if "duration_minutes" in changes and changes["duration_minutes"] < booked_minutes:
        raise HTTPException(409, "Duration cannot be shorter than already scheduled work")
    if "deadline_at" in changes and changes["deadline_at"] is not None:
        if any(end_aware(b.ends_at) > changes["deadline_at"] for b in scheduled):
            raise HTTPException(409, "New deadline conflicts with existing scheduled sessions")
    if "status" in changes:
        changes["completed_at"] = now if changes["status"] == "completed" else None
    query = update(Task).where(
        Task.id == task_id, Task.owner_uid == uid, Task.version == body.version
    ).values(**changes, version=Task.version + 1)
    changed = db.execute(query)
    if changed.rowcount != 1:
        if db.scalar(select(Task.id).where(Task.id == task_id, Task.owner_uid == uid)) is None:
            raise HTTPException(404, "Not found")
        raise HTTPException(409, "Task has changed; refresh before editing")
    if "status" in changes and changes["status"] in ("completed", "archived"):
        # This is an explicit user action, and stale approved plan undo
        # will fail rather than silently modifying user history.
        db.execute(delete(ScheduleBlock).where(
            ScheduleBlock.owner_uid == uid, ScheduleBlock.task_id == task_id,
            ScheduleBlock.starts_at >= now,
        ))
    db.commit()
    return _owned(db, Task, uid, task_id)


def end_aware(value: datetime) -> datetime:
    return value if value.tzinfo and value.utcoffset() is not None else value.replace(tzinfo=timezone.utc)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    db.scalar(select(User).where(User.uid == uid).with_for_update())
    row = _owned(db, Task, uid, task_id)
    if db.scalar(select(ScheduleBlock.id).where(
        ScheduleBlock.owner_uid == uid, ScheduleBlock.task_id == task_id
    ).limit(1)) is not None:
        raise HTTPException(409, "This task has scheduled sessions. Undo or remove them before deletion.")
    if db.scalar(select(RecurrenceOccurrence.id).where(
        RecurrenceOccurrence.owner_uid == uid, RecurrenceOccurrence.task_id == task_id
    ).limit(1)) is not None:
        raise HTTPException(409, "Recurring task occurrences should be archived or skipped, not deleted.")
    db.execute(delete(TaskDependency).where(
        TaskDependency.owner_uid == uid,
        (TaskDependency.task_id == task_id) | (TaskDependency.depends_on_id == task_id),
    ))
    db.execute(update(FocusSession).where(
        FocusSession.owner_uid == uid, FocusSession.task_id == task_id
    ).values(task_id=None))
    db.execute(update(InAppNotification).where(
        InAppNotification.owner_uid == uid, InAppNotification.source_task_id == task_id
    ).values(source_task_id=None))
    db.delete(row)
    db.commit()


@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    get_or_create_user(db, uid)
    row = db.get(Preference, uid)
    if row is None:
        row = Preference(owner_uid=uid)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/preferences", response_model=PreferencesOut)
def put_preferences(body: PreferencesUpdate, user: dict = Depends(get_current_user), db: Session = Depends(get_session)):
    uid = user["uid"]
    account = get_or_create_user(db, uid)
    row = db.get(Preference, uid)
    if row is None:
        row = Preference(owner_uid=uid)
        db.add(row)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    account.timezone = body.timezone
    db.commit()
    db.refresh(row)
    return row
