"""ChromaDB-backed semantic search over products."""
from __future__ import annotations

from typing import Optional

from app.db.chroma import get_collection
from app.services.ollama_service import get_ollama


class VectorService:
    async def upsert_product(
        self,
        *,
        slug: str,
        document: str,
        metadata: dict,
    ) -> None:
        embedding = await get_ollama().embed(document)
        coll = get_collection()
        coll.upsert(
            ids=[slug],
            embeddings=[embedding],
            documents=[document],
            metadatas=[metadata],
        )

    async def search(
        self,
        query: str,
        *,
        top_k: int = 12,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        price_range: Optional[tuple[float, float]] = None,
    ) -> list[dict]:
        embedding = await get_ollama().embed(query)
        coll = get_collection()

        # Chroma 1.x requires exactly one operator per condition; combine with $and.
        clauses: list[dict] = []
        if category:
            clauses.append({"category": {"$eq": category}})
        if brand:
            clauses.append({"brand": {"$eq": brand}})
        if price_range:
            lo, hi = price_range
            if lo > 0:
                clauses.append({"price": {"$gte": lo}})
            if hi < 1e12:
                clauses.append({"price": {"$lte": hi}})
        where: dict | None
        if len(clauses) == 0:
            where = None
        elif len(clauses) == 1:
            where = clauses[0]
        else:
            where = {"$and": clauses}

        results = coll.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
        )
        slugs = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0] or [0] * len(slugs)
        metadatas = results.get("metadatas", [[]])[0] or [{}] * len(slugs)
        return [
            {"slug": s, "score": 1.0 - d, "metadata": m}
            for s, d, m in zip(slugs, distances, metadatas)
        ]


_vector: VectorService | None = None


def get_vector() -> VectorService:
    global _vector
    if _vector is None:
        _vector = VectorService()
    return _vector
