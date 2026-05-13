"""Seed ~2200 procedural products into MongoDB + ChromaDB.

Usage:
    python -m scripts.seed_products              # full pipeline
    python -m scripts.seed_products --no-embed   # Mongo only, skip embeddings
    python -m scripts.seed_products --reset      # drop + recreate

Embeddings run in parallel batches via Ollama. ~5-10 minutes on a modern Mac.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from pymongo import UpdateOne  # noqa: E402

from app.db.chroma import get_collection, init_chroma  # noqa: E402
from app.db.mongodb import close_mongo, connect_mongo, get_db  # noqa: E402
from app.services.ollama_service import get_ollama  # noqa: E402
from scripts.generate_products import generate_products  # noqa: E402


CONCURRENCY = 8        # parallel embedding requests to Ollama
CHROMA_BATCH = 100     # docs per Chroma upsert


def _doc_text(p: dict) -> str:
    return " ".join(
        [
            p["title"],
            p.get("brand", ""),
            p["category"],
            p.get("subcategory", ""),
            p["description"],
            " ".join(p.get("tags", [])),
        ]
    )


async def _bulk_upsert_mongo(products: list[dict]) -> None:
    db = get_db()
    now = datetime.utcnow()
    ops = []
    for p in products:
        p = {**p, "created_at": now}
        ops.append(UpdateOne({"slug": p["slug"]}, {"$set": p}, upsert=True))
    # Mongo allows 100k ops per bulk write; we're well under.
    res = await db.products.bulk_write(ops, ordered=False)
    print(
        f"   Mongo: matched={res.matched_count} modified={res.modified_count} upserted={len(res.upserted_ids)}"
    )


async def _embed_worker(
    queue: asyncio.Queue,
    out: list[tuple[str, str, dict, list[float]]],
    progress: dict,
) -> None:
    ollama = get_ollama()
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            return
        slug, text, meta = item
        try:
            vec = await ollama.embed(text)
            out.append((slug, text, meta, vec))
        except Exception as e:
            print(f"   embed error {slug}: {e}")
        progress["done"] += 1
        if progress["done"] % 50 == 0 or progress["done"] == progress["total"]:
            elapsed = time.time() - progress["t0"]
            rate = progress["done"] / max(elapsed, 0.001)
            remaining = (progress["total"] - progress["done"]) / max(rate, 0.001)
            print(
                f"   [{progress['done']}/{progress['total']}] "
                f"{rate:.1f}/s — eta {remaining:.0f}s"
            )
        queue.task_done()


async def _embed_all(products: list[dict]) -> None:
    init_chroma()
    coll = get_collection()
    queue: asyncio.Queue = asyncio.Queue(maxsize=CONCURRENCY * 4)
    out: list[tuple[str, str, dict, list[float]]] = []
    progress = {"done": 0, "total": len(products), "t0": time.time()}

    workers = [
        asyncio.create_task(_embed_worker(queue, out, progress))
        for _ in range(CONCURRENCY)
    ]

    for p in products:
        await queue.put(
            (
                p["slug"],
                _doc_text(p),
                {
                    "title": p["title"],
                    "category": p["category"],
                    "brand": p.get("brand", ""),
                    "price": float(p["price"]),
                    "rating": float(p["rating"]),
                },
            )
        )
    # Sentinels to stop workers
    for _ in range(CONCURRENCY):
        await queue.put(None)
    await queue.join()
    await asyncio.gather(*workers, return_exceptions=True)

    # Flush to Chroma in batches
    print(f"   Flushing {len(out)} embeddings to Chroma in batches of {CHROMA_BATCH}…")
    for i in range(0, len(out), CHROMA_BATCH):
        chunk = out[i : i + CHROMA_BATCH]
        coll.upsert(
            ids=[c[0] for c in chunk],
            embeddings=[c[3] for c in chunk],
            documents=[c[1] for c in chunk],
            metadatas=[c[2] for c in chunk],
        )
    print("   Chroma flush done.")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-embed", action="store_true", help="Skip Chroma embedding step")
    parser.add_argument("--reset", action="store_true", help="Drop existing collections first")
    parser.add_argument("--embed-only", action="store_true", help="Skip Mongo, just embed existing products into Chroma")
    args = parser.parse_args()

    print("→ Connecting to Mongo…")
    await connect_mongo()
    db = get_db()

    if args.reset:
        print("→ Dropping products collection…")
        await db.products.drop()
        try:
            init_chroma()
            from app.db.chroma import Vector
            if Vector.client is not None:
                Vector.client.delete_collection(get_collection().name)
            init_chroma()
        except Exception as e:
            print(f"   (chroma reset note: {e})")

    if args.embed_only:
        print("→ Loading products from MongoDB…")
        cursor = db.products.find({})
        products = [d async for d in cursor]
        for p in products:
            p.pop("_id", None)
        print(f"   {len(products)} products loaded.")
    else:
        print("→ Generating products…")
        products = generate_products()
        print(f"   {len(products)} products generated.")

        print("→ Bulk-upserting into MongoDB…")
        await _bulk_upsert_mongo(products)

    if args.no_embed:
        print("→ Skipping embeddings (--no-embed).")
    else:
        print(f"→ Embedding into ChromaDB with concurrency={CONCURRENCY}…")
        await _embed_all(products)

    print("✓ Seed complete.")
    await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
