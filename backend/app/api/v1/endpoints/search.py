from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.schemas.product import ProductOut, SearchQuery
from app.services.product_service import get_product_service
from app.services.vector_service import get_vector

router = APIRouter(prefix="/search", tags=["search"])


class Suggestion(BaseModel):
    slug: str
    title: str
    image_url: str
    price: float
    category: str


@router.post("", response_model=list[ProductOut])
async def semantic_search(body: SearchQuery):
    price_range = None
    if body.min_price is not None or body.max_price is not None:
        price_range = (body.min_price or 0.0, body.max_price or 1e12)
    hits = await get_vector().search(
        body.q, top_k=body.top_k, category=body.category, price_range=price_range
    )
    return await get_product_service().get_many([h["slug"] for h in hits])


@router.get("/suggest", response_model=list[Suggestion])
async def suggest(q: str = Query(..., min_length=1), k: int = Query(default=6, ge=1, le=10)):
    """Lightweight typeahead — vector search trimmed to a small payload."""
    hits = await get_vector().search(q, top_k=k)
    products = await get_product_service().get_many([h["slug"] for h in hits])
    return [
        {
            "slug": p["slug"],
            "title": p["title"],
            "image_url": p["image_url"],
            "price": p["price"],
            "category": p["category"],
        }
        for p in products
    ]
