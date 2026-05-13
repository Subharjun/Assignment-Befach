from typing import Optional
from pydantic import BaseModel


class ProductOut(BaseModel):
    slug: str
    title: str
    description: str
    brand: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    price: float
    currency: str = "INR"
    rating: float
    rating_count: int
    image_url: str
    images: list[str] = []
    tags: list[str] = []
    stock: int = 0


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int


class SearchQuery(BaseModel):
    q: str
    top_k: int = 12
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
