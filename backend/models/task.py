"""Validated legacy task request schema (local wall clock in Asia/Kolkata)."""
import re
from datetime import date as calendar_date
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

TIME_PATTERN = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
DAY_CODES = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}


def valid_title(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 120:
        raise ValueError("title must contain 1-120 non-whitespace characters")
    return cleaned


def valid_date(value: str) -> str:
    try:
        parsed = calendar_date.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("date must be a real calendar date in YYYY-MM-DD format") from exc
    if parsed.isoformat() != value:
        raise ValueError("date must use YYYY-MM-DD format")
    return value


def valid_time(value: str) -> str:
    if not isinstance(value, str) or not TIME_PATTERN.fullmatch(value):
        raise ValueError("time must use HH:MM 24-hour format")
    return value


def valid_importance(value: str) -> str:
    if value not in ("important", "not_important"):
        raise ValueError("importance must be important or not_important")
    return value


def valid_recurrence(value: str) -> str:
    if value in ("none", "daily", "weekly"):
        return value
    parts = [part.strip().lower() for part in value.split(",")]
    if not parts or len(parts) != len(set(parts)) or any(part not in DAY_CODES for part in parts):
        raise ValueError("recurrence must be none, daily, weekly, or distinct weekday codes")
    return ",".join(parts)


def validate_duration(start: str, end: str):
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    duration = (eh * 60 + em) - (sh * 60 + sm)
    if duration < 15:
        raise ValueError("Task duration must be at least 15 minutes")
    return duration


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    date: str
    start_time: str
    end_time: str
    importance: str = "important"
    recurrence: str = "none"

    @field_validator("title")
    @classmethod
    def check_title(cls, value):
        return valid_title(value)

    @field_validator("date")
    @classmethod
    def check_date(cls, value):
        return valid_date(value)

    @field_validator("start_time", "end_time")
    @classmethod
    def check_time(cls, value):
        return valid_time(value)

    @field_validator("importance")
    @classmethod
    def check_importance(cls, value):
        return valid_importance(value)

    @field_validator("recurrence")
    @classmethod
    def check_recurrence(cls, value):
        return valid_recurrence(value)

    @model_validator(mode="after")
    def check_duration(self):
        validate_duration(self.start_time, self.end_time)
        return self


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    importance: Optional[str] = None
    recurrence: Optional[str] = None

    @field_validator("title")
    @classmethod
    def check_title(cls, value):
        return valid_title(value) if value is not None else None

    @field_validator("date")
    @classmethod
    def check_date(cls, value):
        return valid_date(value) if value is not None else None

    @field_validator("start_time", "end_time")
    @classmethod
    def check_time(cls, value):
        return valid_time(value) if value is not None else None

    @field_validator("importance")
    @classmethod
    def check_importance(cls, value):
        return valid_importance(value) if value is not None else None

    @field_validator("recurrence")
    @classmethod
    def check_recurrence(cls, value):
        return valid_recurrence(value) if value is not None else None


class StatsResponse(BaseModel):
    total_created: int
    completed: int
    rescheduled: int
    current_streak: int
