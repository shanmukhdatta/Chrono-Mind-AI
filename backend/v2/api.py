"""Authenticated PostgreSQL V2 APIs; legacy Firestore routes stay unchanged."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_or_create_user, get_session
from .models import Goal, Task, Preference
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
    changes = body.model_dump(exclude_unset=True, exclude={"version"})
    for key in ("title", "description", "duration_minutes", "importance", "status"):
        if key in changes and changes[key] is None:
            raise HTTPException(422, key + " cannot be null")
    if "title" in changes and not changes["title"].strip():
        raise HTTPException(422, "Title cannot be blank")
    if "goal_id" in changes:
        _check_goal(db, uid, changes["goal_id"])
    if "status" in changes:
        changes["completed_at"] = datetime.now(timezone.utc) if changes["status"] == "completed" else None
    query = update(Task).where(
        Task.id == task_id, Task.owner_uid == uid, Task.version == body.version
    ).values(**changes, version=Task.version + 1)
    changed = db.execute(query)
    if changed.rowcount != 1:
        if db.scalar(select(Task.id).where(Task.id == task_id, Task.owner_uid == uid)) is None:
            raise HTTPException(404, "Not found")
        raise HTTPException(409, "Task has changed; refresh before editing")
    db.commit()
    return _owned(db, Task, uid, task_id)


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
