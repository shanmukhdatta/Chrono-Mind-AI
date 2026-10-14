"""Relational V2 schema. Logical tasks and schedule blocks are separate entities."""
from datetime import datetime, date, time, timezone
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey, Index, Integer,
    String, Text, Time, UniqueConstraint, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "v2_users"
    uid: Mapped[str] = mapped_column(String(128), primary_key=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Goal(Base):
    __tablename__ = "v2_goals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="active", nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (CheckConstraint("status IN ('active','paused','completed','archived')", name="goal_status"),)


class Task(Base):
    __tablename__ = "v2_tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    goal_id: Mapped[str | None] = mapped_column(ForeignKey("v2_goals.id", ondelete="SET NULL"), nullable=True)
    legacy_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    importance: Mapped[str] = mapped_column(String(24), default="important", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recurrence_rule: Mapped[str | None] = mapped_column(String(160), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        UniqueConstraint("owner_uid", "legacy_id", name="uq_v2_owner_legacy_task"),
        CheckConstraint("duration_minutes > 0", name="task_positive_duration"),
        CheckConstraint("status IN ('pending','completed','archived')", name="task_status"),
        CheckConstraint("importance IN ('important','not_important')", name="task_importance"),
        Index("ix_v2_tasks_owner_status_deadline", "owner_uid", "status", "deadline_at"),
    )


class ScheduleBlock(Base):
    __tablename__ = "v2_schedule_blocks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("v2_tasks.id", ondelete="CASCADE"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="schedule_order"),
        Index("ix_v2_blocks_owner_start", "owner_uid", "starts_at"),
    )


class FixedEvent(Base):
    __tablename__ = "v2_fixed_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="fixed_event_order"),
        Index("ix_v2_events_owner_start", "owner_uid", "starts_at"),
    )


class Preference(Base):
    __tablename__ = "v2_preferences"
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), primary_key=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    work_start: Mapped[time] = mapped_column(Time, default=lambda: time(8, 0), nullable=False)
    work_end: Mapped[time] = mapped_column(Time, default=lambda: time(22, 0), nullable=False)
    max_daily_minutes: Mapped[int] = mapped_column(Integer, default=480, nullable=False)
    min_break_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    __table_args__ = (
        CheckConstraint("work_end > work_start", name="preference_work_window"),
        CheckConstraint("max_daily_minutes BETWEEN 60 AND 960", name="preference_daily_limit"),
    )
