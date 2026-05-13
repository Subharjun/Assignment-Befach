from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.core.security import get_optional_user_id
from app.schemas.product import ProductOut
from app.services.recommendation_service import get_recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/related/{slug}", response_model=list[ProductOut])
async def related(slug: str, k: int = Query(default=8, ge=1, le=20)):
    return await get_recommendation_service().related_to_product(slug, k=k)


@router.get("/for-you", response_model=list[ProductOut])
async def for_you(
    k: int = Query(default=12, ge=1, le=24),
    user_id: Optional[str] = Depends(get_optional_user_id),
):
    return await get_recommendation_service().personalized(user_id, k=k)
