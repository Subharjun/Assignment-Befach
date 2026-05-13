from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    products: List[str] = []   # product slugs surfaced with this turn
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    user_id: str
    session_id: str
    messages: List[Message] = []
    extracted_preferences: dict = {}   # e.g. {"budget": 80000, "use_cases": ["gaming","editing"]}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
