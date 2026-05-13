from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Product(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    slug: str
    title: str
    description: str
    brand: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    price: float
    currency: str = "INR"
    rating: float = 0.0
    rating_count: int = 0
    image_url: str
    images: list[str] = []
    tags: list[str] = []
    attributes: dict = {}
    stock: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
