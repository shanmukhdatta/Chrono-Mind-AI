"""Relational V2 schema. Logical tasks and schedule blocks are separate entities."""
from datetime import datetime, date, time, timezone
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Float, ForeignKey, Index, Integer, JSON,
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
    splittable: Mapped[bool] = mapped_column(default=True, nullable=False)
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
    source: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
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


class PlanProposal(Base):
    """Durable user-owned schedule proposal, never applied without approval."""
    __tablename__ = "v2_plan_proposals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False)
    proposed_blocks: Mapped[list] = mapped_column(JSON, nullable=False)
    unscheduled: Mapped[list] = mapped_column(JSON, nullable=False)
    task_versions: Mapped[dict] = mapped_column(JSON, nullable=False)
    planning_trace: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    preferences_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    committed_block_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("status IN ('pending','approved','rejected','undone')", name="proposal_status"),
        Index("ix_v2_proposals_owner_created", "owner_uid", "created_at"),
    )


class LegacyTaskArchive(Base):
    """Audit-only original V1 data for non-destructive migration/reconciliation."""
    __tablename__ = "v2_legacy_task_archive"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    legacy_id: Mapped[str] = mapped_column(String(128), nullable=False)
    original_json: Mapped[str] = mapped_column(Text, nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (UniqueConstraint("owner_uid", "legacy_id", name="uq_v2_legacy_archive_owner_id"),)


class RecurrenceSeries(Base):
    __tablename__ = "v2_recurrence_series"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    importance: Mapped[str] = mapped_column(String(24), nullable=False)
    frequency: Mapped[str] = mapped_column(String(12), nullable=False)
    weekdays: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    due_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    __table_args__ = (
        CheckConstraint("frequency IN ('daily','weekly')", name="recurrence_frequency"),
        CheckConstraint("duration_minutes BETWEEN 1 AND 1440", name="recurrence_duration"),
        CheckConstraint("importance IN ('important','not_important')", name="recurrence_importance"),
    )


class RecurrenceOccurrence(Base):
    __tablename__ = "v2_recurrence_occurrences"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    series_id: Mapped[str] = mapped_column(ForeignKey("v2_recurrence_series.id"), nullable=False)
    occurrence_date: Mapped[date] = mapped_column(Date, nullable=False)
    task_id: Mapped[str] = mapped_column(ForeignKey("v2_tasks.id"), nullable=False)
    __table_args__ = (UniqueConstraint("series_id","occurrence_date",name="uq_v2_recurrence_occurrence"),)


class RecurrenceSkip(Base):
    __tablename__ = "v2_recurrence_skips"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    series_id: Mapped[str] = mapped_column(ForeignKey("v2_recurrence_series.id"), nullable=False)
    occurrence_date: Mapped[date] = mapped_column(Date, nullable=False)
    __table_args__ = (UniqueConstraint("series_id","occurrence_date",name="uq_v2_recurrence_skip"),)


class BehaviorConsent(Base):
    __tablename__ = "v2_behavior_consent"
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class FocusSession(Base):
    __tablename__ = "v2_focus_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(ForeignKey("v2_tasks.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    planned_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=1500)
    actual_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        CheckConstraint("status IN ('active','completed','abandoned')", name="focus_status"),
        CheckConstraint("planned_seconds BETWEEN 60 AND 14400", name="focus_planned_bounds"),
        Index("ix_v2_focus_owner_started", "owner_uid", "started_at"),
    )


class BehaviorEvent(Base):
    __tablename__ = "v2_behavior_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    hour_of_day: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        CheckConstraint("hour_of_day BETWEEN 0 AND 23", name="behavior_valid_hour"),
        CheckConstraint("duration_seconds >= 0", name="behavior_valid_duration"),
    )


class InAppNotification(Base):
    """One user-scoped notification per source, date, and event kind."""
    __tablename__ = "v2_inapp_notifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    dedupe_key: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    source_task_id: Mapped[str | None] = mapped_column(ForeignKey("v2_tasks.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (
        UniqueConstraint("owner_uid", "dedupe_key", name="uq_v2_notification_owner_key"),
        Index("ix_v2_notification_owner_created", "owner_uid", "created_at"),
    )


class TaskDependency(Base):
    """A task may start only once the referenced prerequisite is completed."""
    __tablename__ = "v2_task_dependencies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("v2_tasks.id", ondelete="CASCADE"), nullable=False)
    depends_on_id: Mapped[str] = mapped_column(ForeignKey("v2_tasks.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (
        UniqueConstraint("owner_uid", "task_id", "depends_on_id", name="uq_v2_task_dependency"),
        CheckConstraint("task_id <> depends_on_id", name="task_no_self_dependency"),
        Index("ix_v2_dependency_owner_task", "owner_uid", "task_id"),
    )


class PlanningDecisionLog(Base):
    """User-owned append-only decision records; never store raw LLM prompts."""
    __tablename__ = "v2_planning_decision_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("v2_plan_proposals.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_codes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    before_blocks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    after_blocks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (Index("ix_v2_decision_owner_date", "owner_uid", "recorded_at"),)


class AssistantMetric(Base):
    """Token/latency metadata only. Never store raw prompts or assistant replies."""
    __tablename__ = "v2_assistant_metrics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_uid: Mapped[str] = mapped_column(ForeignKey("v2_users.uid"), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(24), nullable=False)
    mode: Mapped[str] = mapped_column(String(24), nullable=False)
    model_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (Index("ix_v2_llm_metrics_owner_date", "owner_uid", "recorded_at"),)
