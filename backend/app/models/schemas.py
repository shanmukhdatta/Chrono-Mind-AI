"""
ChronoMind AI — Pydantic Request/Response Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models.models import TaskCategory, TaskStatus, Chronotype


# ─── Auth ─────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthCode(BaseModel):
    code: str
    redirect_uri: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    chronotype: Chronotype = Chronotype.FLEXIBLE
    break_style: str = "pomodoro"
    default_study_duration: int = 90
    preferred_start_hour: int = 8
    preferred_end_hour: int = 22
    is_onboarded: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    chronotype: Optional[Chronotype] = None
    break_style: Optional[str] = None
    default_study_duration: Optional[int] = None
    default_break_duration: Optional[int] = None
    preferred_start_hour: Optional[int] = None
    preferred_end_hour: Optional[int] = None
    is_onboarded: Optional[bool] = None


# ─── Timetable ────────────────────────────────────────────────────

class TimetableEntryCreate(BaseModel):
    day_of_week: str
    start_time: str  # HH:MM
    end_time: str    # HH:MM
    subject: str
    location: Optional[str] = None
    color: Optional[str] = "#F4A261"


class TimetableEntryOut(TimetableEntryCreate):
    id: str
    user_id: str
    is_recurring: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TimetableUploadResult(BaseModel):
    success: bool
    entries: List[TimetableEntryCreate]
    raw_json: Dict[str, Any]
    confidence: float
    message: str


# ─── Tasks ────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: TaskCategory = TaskCategory.STUDY
    duration_minutes: int = 60
    deadline: Optional[datetime] = None
    scheduled_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TaskCategory] = None
    status: Optional[TaskStatus] = None
    duration_minutes: Optional[int] = None
    deadline: Optional[datetime] = None
    scheduled_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class TaskOut(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    category: TaskCategory
    status: TaskStatus
    scheduled_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: int
    deadline: Optional[datetime] = None
    ai_placed: bool = False
    ai_reasoning: Optional[str] = None
    priority_score: float = 0.5
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Chat / AI ────────────────────────────────────────────────────

class ChatMessageIn(BaseModel):
    content: str
    voice_mode: bool = False


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default=None, validation_alias="meta_data")
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentResponse(BaseModel):
    message: str
    tasks_created: List[TaskOut] = []
    tasks_updated: List[TaskOut] = []
    slots_found: List[Dict[str, Any]] = []
    action_type: str = "chat"  # chat | schedule | reschedule | query
    metadata: Dict[str, Any] = {}


# ─── Dashboard ────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    slots_found_this_week: int
    tasks_ai_scheduled: int
    completion_rate: float
    tasks_today: int
    tasks_pending: int
    tasks_completed: int
    streak_days: int


class CalendarDay(BaseModel):
    date: str  # YYYY-MM-DD
    timetable: List[TimetableEntryOut]
    tasks: List[TaskOut]
    free_slots: List[Dict[str, Any]]  # [{start, end, duration_minutes}]


# Update forward reference
Token.model_rebuild()
