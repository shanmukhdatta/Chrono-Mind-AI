"""Authenticated task prerequisite graph with cycle prevention and versioning."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from .db import get_session
from .models import Task, TaskDependency, User

router = APIRouter(prefix="/api/v2/tasks", tags=["v2-dependencies"])


class NewDependency(BaseModel):
    depends_on_id: str


def _task(db: Session, uid: str, task_id: str) -> Task:
    row = db.scalar(select(Task).where(Task.id == task_id, Task.owner_uid == uid))
    if row is None:
        raise HTTPException(404, "Task not found")
    return row


def _lock_user(db: Session, uid: str):
    if db.scalar(select(User.uid).where(User.uid == uid).with_for_update()) is None:
        raise HTTPException(404, "User not found")


def would_create_cycle(
    edges: list[tuple[str, str]], task_id: str, depends_on_id: str
) -> bool:
    """Adding task -> depends_on is cyclic if depends_on already reaches task."""
    adjacency: dict[str, set[str]] = {}
    for dependent, prerequisite in edges:
        adjacency.setdefault(dependent, set()).add(prerequisite)
    stack = [depends_on_id]
    visited = set()
    while stack:
        node = stack.pop()
        if node == task_id:
            return True
        if node in visited:
            continue
        visited.add(node)
        stack.extend(adjacency.get(node, set()) - visited)
    return False


@router.get("/{task_id}/dependencies")
def get_dependencies(
    task_id: str, user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    _task(db, uid, task_id)
    rows = db.scalars(select(TaskDependency).where(
        TaskDependency.owner_uid == uid, TaskDependency.task_id == task_id
    )).all()
    prerequisites = {}
    if rows:
        prerequisites = {
            item.id: item for item in db.scalars(select(Task).where(
                Task.owner_uid == uid, Task.id.in_([row.depends_on_id for row in rows])
            )).all()
        }
    return [
        {"task_id": task_id, "depends_on_id": row.depends_on_id,
         "title": prerequisites[row.depends_on_id].title if row.depends_on_id in prerequisites else "Unavailable",
         "status": prerequisites[row.depends_on_id].status if row.depends_on_id in prerequisites else "missing"}
        for row in rows
    ]


@router.post("/{task_id}/dependencies", status_code=201)
def add_dependency(
    task_id: str, body: NewDependency,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    _lock_user(db, uid)
    dependent = _task(db, uid, task_id)
    prerequisite = _task(db, uid, body.depends_on_id)
    if dependent.id == prerequisite.id:
        raise HTTPException(422, "A task cannot depend on itself")
    if dependent.status != "pending":
        raise HTTPException(409, "Only pending tasks can receive prerequisites")
    existing = db.scalar(select(TaskDependency.id).where(
        TaskDependency.owner_uid == uid,
        TaskDependency.task_id == task_id,
        TaskDependency.depends_on_id == body.depends_on_id,
    ))
    if existing:
        return {"task_id": task_id, "depends_on_id": body.depends_on_id, "already_exists": True}
    edges = db.execute(select(TaskDependency.task_id, TaskDependency.depends_on_id).where(
        TaskDependency.owner_uid == uid
    )).all()
    if would_create_cycle(list(edges), task_id, body.depends_on_id):
        raise HTTPException(409, "This prerequisite would create a dependency cycle")
    db.add(TaskDependency(
        owner_uid=uid, task_id=task_id, depends_on_id=body.depends_on_id
    ))
    # Pending proposals freeze Task.version: changing prerequisites invalidates them.
    dependent.version += 1
    db.commit()
    return {"task_id": task_id, "depends_on_id": body.depends_on_id, "already_exists": False}


@router.delete("/{task_id}/dependencies/{depends_on_id}", status_code=204)
def remove_dependency(
    task_id: str, depends_on_id: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    uid = user["uid"]
    _lock_user(db, uid)
    dependent = _task(db, uid, task_id)
    edge = db.scalar(select(TaskDependency).where(
        TaskDependency.owner_uid == uid,
        TaskDependency.task_id == task_id,
        TaskDependency.depends_on_id == depends_on_id,
    ))
    if edge is None:
        raise HTTPException(404, "Dependency not found")
    db.delete(edge)
    dependent.version += 1
    db.commit()
