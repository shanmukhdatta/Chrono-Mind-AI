from pydantic import BaseModel, field_validator, model_validator
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    importance: str = 'important'
    recurrence: str = 'none'

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Title cannot be empty')
        return v[:120]

    @field_validator('importance')
    @classmethod
    def valid_importance(cls, v):
        if v not in ('important', 'not_important'):
            raise ValueError('importance must be important or not_important')
        return v

    @field_validator('date')
    @classmethod
    def valid_date(cls, v):
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('date must be YYYY-MM-DD format')
        return v

    @field_validator('start_time', 'end_time')
    @classmethod
    def valid_time(cls, v):
        import re
        if not re.match(r'^([01]\d|2[0-3]):[0-5]\d$', v):
            raise ValueError('time must be HH:MM format (24h)')
        return v

    @model_validator(mode='after')
    def end_after_start(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        return self

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    importance: Optional[str] = None
    recurrence: Optional[str] = None

class StatsResponse(BaseModel):
    total_created: int
    completed: int
    rescheduled: int
    current_streak: int
