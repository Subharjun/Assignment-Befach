from pydantic import BaseModel
from typing import List
from app.models.cart import CartItem


class AddToCartIn(BaseModel):
    slug: str
    qty: int = 1


class UpdateCartItemIn(BaseModel):
    slug: str
    qty: int


class CartOut(BaseModel):
    items: List[CartItem]
    subtotal: float
    count: int
