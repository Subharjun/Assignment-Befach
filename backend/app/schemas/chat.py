from typing import List, Literal, Optional
from pydantic import BaseModel
from app.schemas.product import ProductOut


class ChatTurnIn(BaseModel):
    session_id: str
    message: str


class ChatMessageOut(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    products: List[ProductOut] = []


class ChatTurnOut(BaseModel):
    session_id: str
    reply: str
    products: List[ProductOut] = []
    follow_up: Optional[str] = None
    preferences: dict = {}


class ConversationOut(BaseModel):
    session_id: str
    messages: List[ChatMessageOut]
    extracted_preferences: dict = {}
