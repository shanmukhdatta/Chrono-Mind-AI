"""
ChronoMind AI — Auth Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.models.database import get_db
from app.models.schemas import UserCreate, UserLogin, Token, GoogleAuthCode, UserOut
from app.services.auth_service import (
    create_user, get_user_by_email, verify_password,
    create_access_token, exchange_google_code,
    get_google_user_info, get_or_create_google_user,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await create_user(db, data)
    token = create_access_token({"sub": user.id})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.id})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/google", response_model=Token)
async def google_auth(data: GoogleAuthCode, db: AsyncSession = Depends(get_db)):
    try:
        tokens = await exchange_google_code(data.code, data.redirect_uri)
        google_info = await get_google_user_info(tokens["access_token"])
        user = await get_or_create_google_user(db, google_info)
        token = create_access_token({"sub": user.id})
        return Token(access_token=token, user=UserOut.model_validate(user))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google auth failed: {str(e)}")


@router.post("/demo", response_model=Token)
async def demo_login(db: AsyncSession = Depends(get_db)):
    """Create/login as demo user for testing."""
    demo_email = "rohan.kumar@demo.chronomind.ai"
    user = await get_user_by_email(db, demo_email)

    if not user:
        from app.models.schemas import UserCreate as UC
        user = await create_user(db, UC(
            email=demo_email,
            name="Rohan Kumar",
            password="demo1234",
        ))
        user.institution = "IIT Delhi"
        user.year = "2nd Year B.Tech"
        user.is_onboarded = True
        await db.flush()
        await db.refresh(user)
        await _seed_demo_data(db, user.id)
    # If user exists, just return token — do NOT re-seed

    token = create_access_token({"sub": user.id})
    return Token(access_token=token, user=UserOut.model_validate(user))


async def _seed_demo_data(db: AsyncSession, user_id: str):
    """Seed demo timetable and tasks."""
    from app.models.models import TimetableEntry, Task, TaskCategory, TaskStatus
    from datetime import date, datetime, timedelta

    demo_tt = [
        ("Monday", "09:00", "10:00", "Mathematics", "LH-1"),
        ("Monday", "11:00", "13:00", "Physics Lab", "Lab-3"),
        ("Monday", "14:00", "15:00", "Data Structures", "LH-2"),
        ("Tuesday", "09:00", "10:00", "Control Systems", "LH-1"),
        ("Tuesday", "11:00", "12:00", "Signal Processing", "LH-3"),
        ("Wednesday", "09:00", "10:00", "Mathematics", "LH-1"),
        ("Wednesday", "14:00", "15:00", "Data Structures", "LH-2"),
        ("Thursday", "09:00", "10:00", "Control Systems", "LH-1"),
        ("Thursday", "11:00", "13:00", "DS Lab", "Lab-2"),
        ("Friday", "09:00", "10:00", "Mathematics", "LH-1"),
        ("Friday", "11:00", "12:00", "Signal Processing", "LH-3"),
    ]

    colors = {
        "Mathematics": "#E76F51",
        "Physics Lab": "#2A9D8F",
        "Data Structures": "#E9C46A",
        "Control Systems": "#F4A261",
        "Signal Processing": "#264653",
        "DS Lab": "#2A9D8F",
    }

    for day, start, end, subject, location in demo_tt:
        entry = TimetableEntry(
            user_id=user_id, day_of_week=day, start_time=start,
            end_time=end, subject=subject, location=location,
            color=colors.get(subject, "#F4A261"),
        )
        db.add(entry)

    today = date.today()
    demo_tasks = [
        ("DSA Assignment", "Complete all Graph algorithms problems", TaskCategory.ASSIGNMENT, today.isoformat(), "16:00", "18:00", 120, True),
        ("Study for Mid-Sem", "Revise Chapters 1-5 of Data Structures", TaskCategory.STUDY, today.isoformat(), "19:00", "20:30", 90, True),
        ("Morning Run", "5km run in the park", TaskCategory.EXERCISE, (today + timedelta(days=1)).isoformat(), "06:30", "07:15", 45, False),
    ]

    for title, desc, cat, sdate, start, end, dur, ai_placed in demo_tasks:
        task = Task(
            user_id=user_id, title=title, description=desc, category=cat,
            scheduled_date=sdate, start_time=start, end_time=end,
            duration_minutes=dur, ai_placed=ai_placed,
            deadline=datetime.now() + timedelta(days=2),
        )
        db.add(task)

    await db.flush()
