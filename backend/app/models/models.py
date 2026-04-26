"""
ChronoMind AI — SQLAlchemy ORM Models
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Float,
    Text, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum


class Base(DeclarativeBase):
    pass


def gen_uuid():
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────

class TaskCategory(str, enum.Enum):
    STUDY = "study"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    PERSONAL = "personal"
    EXERCISE = "exercise"
    OTHER = "other"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class Chronotype(str, enum.Enum):
    MORNING = "morning"
    NIGHT = "night"
    FLEXIBLE = "flexible"


# ─── User ─────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    institution = Column(String, nullable=True)
    year = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # None for Google OAuth users
    google_id = Column(String, unique=True, nullable=True, index=True)

    # Preferences
    chronotype = Column(SAEnum(Chronotype), default=Chronotype.FLEXIBLE)
    break_style = Column(String, default="pomodoro")  # pomodoro | long
    default_study_duration = Column(Integer, default=90)   # minutes
    default_break_duration = Column(Integer, default=15)   # minutes
    preferred_start_hour = Column(Integer, default=8)
    preferred_end_hour = Column(Integer, default=22)

    is_onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    timetable_entries = relationship("TimetableEntry", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


# ─── Timetable ────────────────────────────────────────────────────

class TimetableEntry(Base):
    __tablename__ = "timetable_entries"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    day_of_week = Column(String, nullable=False)  # Monday, Tuesday, ...
    start_time = Column(String, nullable=False)   # HH:MM (24h)
    end_time = Column(String, nullable=False)     # HH:MM (24h)
    subject = Column(String, nullable=False)
    location = Column(String, nullable=True)
    color = Column(String, default="#F4A261")
    is_recurring = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="timetable_entries")


# ─── Task ─────────────────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SAEnum(TaskCategory), default=TaskCategory.STUDY)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING)

    # Scheduling
    scheduled_date = Column(String, nullable=True)   # YYYY-MM-DD
    start_time = Column(String, nullable=True)       # HH:MM
    end_time = Column(String, nullable=True)         # HH:MM
    duration_minutes = Column(Integer, nullable=False, default=60)
    deadline = Column(DateTime(timezone=True), nullable=True)

    # AI metadata
    ai_placed = Column(Boolean, default=False)
    ai_reasoning = Column(Text, nullable=True)
    priority_score = Column(Float, default=0.5)

    # Completion
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="tasks")


# ─── Chat ─────────────────────────────────────────────────────────

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)   # user | assistant
    content = Column(Text, nullable=False)
    meta_data = Column(JSON, nullable=True)  # tasks created, slots found, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chat_messages")
