from __future__ import annotations

from typing import Optional

from app.db.mongodb import get_db


def _normalize(doc: dict) -> dict:
    if not doc:
        return doc
    doc.pop("_id", None)
    return doc


class ProductService:
    async def list_products(
        self,
        *,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "rating",
    ) -> tuple[list[dict], int]:
        q: dict = {}
        if category:
            q["category"] = category
        db = get_db()
        total = await db.products.count_documents(q)
        sort_field = {"rating": ("rating", -1), "price_asc": ("price", 1), "price_desc": ("price", -1)}.get(
            sort, ("rating", -1)
        )
        cursor = (
            db.products.find(q)
            .sort(*sort_field)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        items = [_normalize(d) async for d in cursor]
        return items, total

    async def get_by_slug(self, slug: str) -> Optional[dict]:
        return _normalize(await get_db().products.find_one({"slug": slug}) or {}) or None

    async def get_many(self, slugs: list[str]) -> list[dict]:
        cursor = get_db().products.find({"slug": {"$in": slugs}})
        by_slug = {d["slug"]: _normalize(d) async for d in cursor}
        # preserve order from `slugs`
        return [by_slug[s] for s in slugs if s in by_slug]

    async def list_categories(self) -> list[str]:
        return sorted(await get_db().products.distinct("category"))


_svc: ProductService | None = None


def get_product_service() -> ProductService:
    global _svc
    if _svc is None:
        _svc = ProductService()
    return _svc
