"""Recommendation engine: blend vector similarity with user preferences/history."""
from __future__ import annotations

from typing import Optional

from app.db.mongodb import get_db
from app.services.product_service import get_product_service
from app.services.vector_service import get_vector


class RecommendationService:
    async def related_to_product(self, slug: str, *, k: int = 8) -> list[dict]:
        product = await get_product_service().get_by_slug(slug)
        if not product:
            return []
        query = f"{product['title']} {product.get('description','')} {' '.join(product.get('tags', []))}"
        hits = await get_vector().search(query, top_k=k + 1)
        hits = [h for h in hits if h["slug"] != slug][:k]
        return await get_product_service().get_many([h["slug"] for h in hits])

    async def personalized(self, user_id: Optional[str], *, k: int = 12) -> list[dict]:
        # Cold start: top-rated mixed across categories.
        if not user_id:
            items, _ = await get_product_service().list_products(page=1, page_size=k, sort="rating")
            return items

        user = await get_db().users.find_one({"clerk_id": user_id})
        history_slugs = (user or {}).get("history", [])[-5:]
        prefs = (user or {}).get("preferences", {})

        # Build a query from preferences + recent history titles.
        seed_titles: list[str] = []
        if history_slugs:
            recent = await get_product_service().get_many(history_slugs)
            seed_titles = [r["title"] for r in recent]
        pref_terms = " ".join(
            [
                *(prefs.get("categories", []) or []),
                *(prefs.get("brands", []) or []),
                *(prefs.get("use_cases", []) or []),
            ]
        )
        query = (" ".join(seed_titles) + " " + pref_terms).strip()
        if not query:
            items, _ = await get_product_service().list_products(page=1, page_size=k, sort="rating")
            return items

        hits = await get_vector().search(query, top_k=k + len(history_slugs))
        keep = [h["slug"] for h in hits if h["slug"] not in set(history_slugs)][:k]
        return await get_product_service().get_many(keep)


_svc: RecommendationService | None = None


def get_recommendation_service() -> RecommendationService:
    global _svc
    if _svc is None:
        _svc = RecommendationService()
    return _svc
