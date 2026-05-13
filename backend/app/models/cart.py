from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class CartItem(BaseModel):
    product_id: str
    slug: str
    title: str
    image_url: str
    price: float
    qty: int = 1


class Cart(BaseModel):
    user_id: str
    items: List[CartItem] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)
