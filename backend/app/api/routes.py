"""
ChronoMind AI — Tasks, Timetable, Dashboard, AI Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.models.database import get_db
from app.models.models import Task, TimetableEntry, ChatMessage, User, TaskStatus, TaskCategory
from app.models.schemas import (
    TaskCreate, TaskOut, TaskUpdate, TimetableEntryCreate, TimetableEntryOut,
    TimetableUploadResult, ChatMessageIn, ChatMessageOut, AgentResponse,
    DashboardStats, CalendarDay, UserOut, UserUpdate
)
from app.utils.dependencies import get_current_user
from app.services.ocr_service import extract_timetable_from_image
from app.services.scheduler_service import get_week_stats, find_free_slots

# ─── User Router ──────────────────────────────────────────────────
user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@user_router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)
    return current_user


# ─── Dashboard Router ─────────────────────────────────────────────
dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@dashboard_router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stats = await get_week_stats(db, current_user.id)
    return DashboardStats(**stats)


@dashboard_router.get("/calendar/{date_str}", response_model=CalendarDay)
async def get_calendar_day(
    date_str: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    day_name = target_date.strftime("%A")

    # Timetable for this day
    tt_result = await db.execute(
        select(TimetableEntry).where(
            and_(
                TimetableEntry.user_id == current_user.id,
                TimetableEntry.day_of_week == day_name,
            )
        )
    )
    timetable = tt_result.scalars().all()

    # Tasks for this date
    task_result = await db.execute(
        select(Task).where(
            and_(Task.user_id == current_user.id, Task.scheduled_date == date_str)
        )
    )
    tasks = task_result.scalars().all()

    # Free slots (30-min minimum)
    free_slots = await find_free_slots(
        db, current_user.id, target_date, 30,
        current_user.preferred_start_hour * 60,
        current_user.preferred_end_hour * 60,
    )

    return CalendarDay(
        date=date_str,
        timetable=[TimetableEntryOut.model_validate(t) for t in timetable],
        tasks=[TaskOut.model_validate(t) for t in tasks],
        free_slots=free_slots,
    )


# ─── Timetable Router ─────────────────────────────────────────────
timetable_router = APIRouter(prefix="/timetable", tags=["timetable"])


@timetable_router.post("/upload", response_model=TimetableUploadResult)
async def upload_timetable(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="File must be an image (JPG/PNG/WebP) or PDF")

    image_bytes = await file.read()
    result = await extract_timetable_from_image(image_bytes, file.filename or "timetable")

    entries = []
    for day, classes in result.get("timetable", {}).items():
        for cls in classes:
            entries.append(TimetableEntryCreate(
                day_of_week=day,
                start_time=cls["start"],
                end_time=cls["end"],
                subject=cls["subject"],
                location=cls.get("location"),
            ))

    return TimetableUploadResult(
        success=True,
        entries=entries,
        raw_json=result.get("timetable", {}),
        confidence=result.get("confidence", 0.8),
        message=f"Extracted {len(entries)} classes from your timetable.",
    )


@timetable_router.post("/save", response_model=List[TimetableEntryOut])
async def save_timetable(
    entries: List[TimetableEntryCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Delete existing timetable
    existing = await db.execute(
        select(TimetableEntry).where(TimetableEntry.user_id == current_user.id)
    )
    for entry in existing.scalars():
        await db.delete(entry)

    # Save new entries
    saved = []
    for e in entries:
        entry = TimetableEntry(user_id=current_user.id, **e.model_dump())
        db.add(entry)
        saved.append(entry)

    await db.flush()
    for s in saved:
        await db.refresh(s)

    return [TimetableEntryOut.model_validate(s) for s in saved]


@timetable_router.get("/", response_model=List[TimetableEntryOut])
async def get_timetable(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TimetableEntry).where(TimetableEntry.user_id == current_user.id)
    )
    return [TimetableEntryOut.model_validate(e) for e in result.scalars()]


# ─── Tasks Router ─────────────────────────────────────────────────
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.post("/", response_model=TaskOut, status_code=201)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = Task(user_id=current_user.id, **data.model_dump())
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return TaskOut.model_validate(task)


@tasks_router.get("/", response_model=List[TaskOut])
async def list_tasks(
    date_str: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).where(Task.user_id == current_user.id)
    if date_str:
        query = query.where(Task.scheduled_date == date_str)
    if status:
        query = query.where(Task.status == status)
    query = query.order_by(Task.scheduled_date, Task.start_time)

    result = await db.execute(query)
    return [TaskOut.model_validate(t) for t in result.scalars()]


@tasks_router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Task).where(and_(Task.id == task_id, Task.user_id == current_user.id))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(task, field, value)

    if data.status == TaskStatus.COMPLETED:
        task.completed_at = datetime.now()

    await db.flush()
    await db.refresh(task)
    return TaskOut.model_validate(task)


@tasks_router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Task).where(and_(Task.id == task_id, Task.user_id == current_user.id))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)


# ─── AI Chat Router ───────────────────────────────────────────────
ai_router = APIRouter(prefix="/ai", tags=["ai"])


@ai_router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(
    data: ChatMessageIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.agents.scheduler_agent import run_agent

    # Get recent chat history
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(desc(ChatMessage.created_at))
        .limit(10)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(history_result.scalars().all())
    ]

    # Run agent
    result = await run_agent(db, current_user, data.content, history)

    # Save messages
    user_msg = ChatMessage(user_id=current_user.id, role="user", content=data.content)
    ai_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=result["message"],
        meta_data={
            "tasks_created": len(result.get("tasks_created", [])),
            "action_type": result.get("action_type", "chat"),
        }
    )
    db.add(user_msg)
    db.add(ai_msg)
    await db.flush()

    return AgentResponse(
        message=result["message"],
        tasks_created=[],  # TaskOut conversion would go here
        tasks_updated=[],
        slots_found=result.get("slots_found", []),
        action_type=result.get("action_type", "chat"),
    )


@ai_router.get("/history", response_model=List[ChatMessageOut])
async def get_chat_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
    )
    return [ChatMessageOut.model_validate(m) for m in result.scalars()]


@ai_router.delete("/history", status_code=204)
async def clear_chat_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.user_id == current_user.id)
    )
    for msg in result.scalars():
        await db.delete(msg)
