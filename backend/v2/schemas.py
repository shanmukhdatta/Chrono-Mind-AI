"""Validated API contracts; never let client choose owner_uid."""
from datetime import date, datetime, time
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def require_aware(value: datetime | None) -> datetime | None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise ValueError("A timezone offset is required")
    return value


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    target_date: date | None = None

    @field_validator("title")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title cannot be blank")
        return value.strip()


class GoalUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=160)
    description: str | None = Field(None, max_length=4000)
    target_date: date | None = None
    status: Literal["active", "paused", "completed", "archived"] | None = None


class GoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str
    status: str
    target_date: date | None


def clean_context_tags(values: list[str] | None) -> list[str]:
    """Normalize up to 5 context tags: trimmed, deduplicated, case-folded order-preserving."""
    if not values:
        return []
    if len(values) > 5:
        raise ValueError("At most 5 context tags are allowed")
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in values:
        tag = " ".join(str(raw).split())
        if not tag:
            raise ValueError("Context tags cannot be blank")
        if len(tag) > 40:
            raise ValueError("Context tags must be 40 characters or fewer")
        key = tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(tag)
    return cleaned


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=4000)
    context_tags: list[str] = Field(default_factory=list, max_length=5)
    duration_minutes: int = Field(default=30, ge=1, le=1440)
    splittable: bool = True
    importance: Literal["important", "not_important"] = "important"
    deadline_at: datetime | None = None
    goal_id: str | None = None
    parent_task_id: str | None = None

    @field_validator("title")
    @classmethod
    def non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Title cannot be blank")
        return value.strip()

    @field_validator("context_tags")
    @classmethod
    def normalized_tags(cls, value: list[str]) -> list[str]:
        return clean_context_tags(value)

    @field_validator("deadline_at")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        return require_aware(value)


class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=160)
    description: str | None = Field(None, max_length=4000)
    context_tags: list[str] | None = Field(None, max_length=5)
    duration_minutes: int | None = Field(None, ge=1, le=1440)
    splittable: bool | None = None
    importance: Literal["important", "not_important"] | None = None
    status: Literal["pending", "completed", "archived"] | None = None
    deadline_at: datetime | None = None
    goal_id: str | None = None
    parent_task_id: str | None = None
    version: int = Field(ge=1)

    @field_validator("deadline_at")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        return require_aware(value)

    @field_validator("context_tags")
    @classmethod
    def normalized_update_tags(cls, value: list[str] | None) -> list[str] | None:
        return None if value is None else clean_context_tags(value)


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str
    context_tags: list[str] = Field(default_factory=list)
    duration_minutes: int
    splittable: bool
    importance: str
    status: str
    deadline_at: datetime | None
    goal_id: str | None
    parent_task_id: str | None = None
    version: int


class PreferencesUpdate(BaseModel):
    timezone: str = "Asia/Kolkata"
    work_start: time = time(8, 0)
    work_end: time = time(22, 0)
    max_daily_minutes: int = Field(default=480, ge=60, le=960)
    min_break_minutes: int = Field(default=10, ge=0, le=120)
    focus_context: str | None = Field(default=None, max_length=64)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Unknown IANA timezone") from exc
        return value

    @field_validator("focus_context")
    @classmethod
    def clean_focus_context(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None

    @model_validator(mode="after")
    def check_window(self):
        if self.work_end <= self.work_start:
            raise ValueError("work_end must be after work_start")
        return self


class PreferencesOut(PreferencesUpdate):
    model_config = ConfigDict(from_attributes=True)
