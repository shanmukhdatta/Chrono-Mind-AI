from pydantic import BaseModel, field_validator
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []

    @field_validator('message')
    @classmethod
    def message_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Message cannot be empty')
        if len(v) > 500:
            raise ValueError('Message must be under 500 characters')
        return v

class ChatResponse(BaseModel):
    reply: str
