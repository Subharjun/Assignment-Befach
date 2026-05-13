"""User profile + browsing history endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user_id
from app.db.mongodb import get_db
from app.services.product_service import get_product_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def me(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    user = await db.users.find_one({"clerk_id": user_id})
    if not user:
        user = {
            "clerk_id": user_id,
            "preferences": {},
            "history": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await db.users.insert_one(user)
    user.pop("_id", None)
    return user


@router.post("/history/{slug}")
async def push_history(slug: str, user_id: str = Depends(get_current_user_id)):
    product = await get_product_service().get_by_slug(slug)
    if not product:
        raise HTTPException(404, "Product not found")
    db = get_db()
    # cap history at 50, no consecutive duplicates
    await db.users.update_one(
        {"clerk_id": user_id},
        {
            "$pull": {"history": slug},
        },
    )
    await db.users.update_one(
        {"clerk_id": user_id},
        {
            "$push": {"history": {"$each": [slug], "$slice": -50}},
            "$set": {"updated_at": datetime.utcnow()},
        },
        upsert=True,
    )
    return {"ok": True}
