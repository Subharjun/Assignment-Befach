from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user_id
from app.db.mongodb import get_db
from app.schemas.cart import AddToCartIn, CartOut, UpdateCartItemIn
from app.services.product_service import get_product_service

router = APIRouter(prefix="/cart", tags=["cart"])


async def _load_cart(user_id: str) -> dict:
    db = get_db()
    cart = await db.carts.find_one({"user_id": user_id})
    if not cart:
        cart = {"user_id": user_id, "items": [], "updated_at": datetime.utcnow()}
        await db.carts.insert_one(cart)
    return cart


def _serialize(cart: dict) -> dict:
    items = cart.get("items", [])
    subtotal = sum(i["price"] * i["qty"] for i in items)
    count = sum(i["qty"] for i in items)
    return {"items": items, "subtotal": subtotal, "count": count}


@router.get("", response_model=CartOut)
async def get_cart(user_id: str = Depends(get_current_user_id)):
    return _serialize(await _load_cart(user_id))


@router.post("/add", response_model=CartOut)
async def add_item(body: AddToCartIn, user_id: str = Depends(get_current_user_id)):
    product = await get_product_service().get_by_slug(body.slug)
    if not product:
        raise HTTPException(404, "Product not found")
    db = get_db()
    cart = await _load_cart(user_id)
    items = cart.get("items", [])
    existing = next((i for i in items if i["slug"] == body.slug), None)
    if existing:
        existing["qty"] += body.qty
    else:
        items.append(
            {
                "product_id": product["slug"],
                "slug": product["slug"],
                "title": product["title"],
                "image_url": product["image_url"],
                "price": product["price"],
                "qty": body.qty,
            }
        )
    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": items, "updated_at": datetime.utcnow()}},
    )
    cart["items"] = items
    return _serialize(cart)


@router.post("/update", response_model=CartOut)
async def update_item(body: UpdateCartItemIn, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    cart = await _load_cart(user_id)
    items = [i for i in cart.get("items", []) if i["slug"] != body.slug or body.qty > 0]
    for i in items:
        if i["slug"] == body.slug:
            i["qty"] = body.qty
    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": items, "updated_at": datetime.utcnow()}},
    )
    cart["items"] = items
    return _serialize(cart)


@router.delete("/{slug}", response_model=CartOut)
async def remove_item(slug: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    cart = await _load_cart(user_id)
    items = [i for i in cart.get("items", []) if i["slug"] != slug]
    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": items, "updated_at": datetime.utcnow()}},
    )
    cart["items"] = items
    return _serialize(cart)
