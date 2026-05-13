from fastapi import APIRouter, HTTPException, Query
from app.schemas.product import ProductListOut, ProductOut
from app.services.product_service import get_product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListOut)
async def list_products(
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=60),
    sort: str = Query(default="rating", pattern="^(rating|price_asc|price_desc)$"),
):
    items, total = await get_product_service().list_products(
        category=category, page=page, page_size=page_size, sort=sort
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/categories", response_model=list[str])
async def list_categories():
    return await get_product_service().list_categories()


@router.get("/{slug}", response_model=ProductOut)
async def get_product(slug: str):
    p = await get_product_service().get_by_slug(slug)
    if not p:
        raise HTTPException(404, "Product not found")
    return p
