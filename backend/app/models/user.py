from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class UserProfile(BaseModel):
    clerk_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    preferences: dict = {}        # learned preferences (categories, brands, price band)
    history: list[str] = []        # product slugs viewed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
