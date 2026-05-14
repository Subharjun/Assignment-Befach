"""AI orchestration: the mall-assistant brain.

Pipeline for a single user turn:
  1. Load short conversation history + extracted preferences.
  2. Use LLM in JSON mode to extract intent, search_query, filters, follow_up.
  3. Run semantic search via ChromaDB (if intent is product-seeking).
  4. Compose grounded reply with product context + ask follow-up if helpful.
  5. Persist messages + merged preferences.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from app.services.chat_llm import get_chat_llm
from app.services.conversation_service import get_conversation_service
from app.services.intent_hints import hint_brand, hint_category
from app.services.product_service import get_product_service
from app.services.vector_service import get_vector


SYSTEM_PROMPT = """You are Maya, a warm and knowledgeable shopping assistant at MayaMall.
You communicate through BOTH voice and text — your replies are read aloud to the user via text-to-speech.
You help shoppers find the right product through natural conversation — like a real human associate.

Behave like this:
- Be concise (2–4 sentences). Friendly, conversational, never robotic.
- You DO have a voice — you speak your replies aloud. Never say you are text-only or don't have a voice.
- If someone asks if you can hear them or speak, confirm warmly that you can speak and are listening.
- If the user's need is vague, ask ONE focused follow-up (budget, use case, brand preference, size).
- Once you understand intent, recommend products from the provided CATALOG_RESULTS only.
- NEVER invent product names, brands, model numbers, prices, or specs.
- Suggest complementary items when natural (laptop → cooling pad, mouse, monitor) — but again, only from CATALOG_RESULTS.
- Reference products by their TITLE in prose.
- Remember and use the user's stated preferences from earlier in the conversation."""

NO_RESULTS_PROMPT = """You are Maya, a warm voice-and-text shopping assistant at MayaMall.
Your replies are read aloud — never say you are text-only. The user just asked for a product
that the catalog does NOT carry — there are zero matches in CATALOG_RESULTS.

ABSOLUTE RULES (do not break, this is the most important instruction):
- DO NOT name any product, brand, model, or price. None. Zero.
- DO NOT say "How about X" or "Here are some options" — there are no options to show.
- DO NOT propose specific alternative products (e.g. "how about guitars instead" or "try yoga blocks").
- DO NOT format anything like "1. {Brand} {Model} | ₹{price} | rating X | tags:" — that template is forbidden.
- Politely tell the user we don't have what they asked for right now.
- You MAY mention only the broad categories we DO carry, from this exact list:
  laptops, mobiles, audio, monitors, accessories, footwear, clothing, beauty, books, kitchen, furniture, eyewear.
- Ask if they'd like to browse one of those categories instead.

Reply in 1–2 short sentences. No lists. No product names."""


INTENT_PROMPT = """You extract shopping intent from a user message. Respond with STRICT JSON only.

Schema:
{
  "intent": "product_search" | "greeting" | "smalltalk" | "compare" | "clarify" | "complementary" | "purchase_decided",
  "search_query": "string — semantic query to feed a vector DB; empty if not searching",
  "category": "string or null",
  "min_price": number or null,
  "max_price": number or null,
  "preferences": { "use_cases": [string], "brands": [string], "budget": number or null },
  "purchase_intent": boolean,
  "complement_for": "Mobiles" | "Laptops" | "Audio" | "Monitors" | "Footwear" | "Clothing" | "Eyewear" | null,
  "follow_up_needed": boolean,
  "follow_up_question": "string — one short question to ask the user, or empty"
}

Rules:
- "intent" is product_search only if the user is asking to find/buy/recommend a product.
- "purchase_intent" is true when the user signals they've decided/bought ("I'll take it", "great I'll buy this", "purchased", "going with this one", "sold", "I want to buy this"). Set intent = "purchase_decided".
- When purchase_intent is true, set complement_for to the category of the just-decided product (inferred from conversation). For phones use "Mobiles", for laptops "Laptops", etc.
- Map numbers like "80k", "80,000", "1.5 lakh" to integers (80000, 80000, 150000).
- A stated "budget" means max_price = budget. Do NOT set min_price unless the user explicitly states a lower bound.
- search_query should be a clean noun phrase ideal for semantic search.
- Keep arrays empty if uncertain; do not hallucinate brands."""


def _parse_json_object(text: str) -> dict:
    """Extract the first JSON object from a model response."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {}


def _merge_preferences(existing: dict, new: dict) -> dict:
    merged = dict(existing or {})
    for key in ("use_cases", "brands"):
        cur = set(merged.get(key, []) or [])
        cur.update(new.get(key, []) or [])
        if cur:
            merged[key] = sorted(cur)
    if new.get("budget"):
        merged["budget"] = new["budget"]
    return merged


def _format_history(messages: list[dict], limit: int = 8) -> list[dict]:
    out = []
    for m in messages[-limit:]:
        role = m.get("role", "user")
        if role not in ("user", "assistant"):
            continue
        out.append({"role": role, "content": m.get("content", "")})
    return out


# Complementary search queries per primary category. After a user signals
# they've decided to buy something from these categories, surface real items
# from our catalog that pair naturally with it.
COMPLEMENT_QUERIES: dict[str, list[tuple[str, str | None]]] = {
    # (semantic query, optional category filter)
    "Mobiles": [
        ("phone case cover", "Accessories"),
        ("phone charger fast charging cable", "Accessories"),
        ("power bank 20000mAh", "Accessories"),
        ("wireless earbuds true wireless", "Audio"),
    ],
    "Laptops": [
        ("laptop cooling pad", "Accessories"),
        ("wireless mouse", "Accessories"),
        ("mechanical keyboard", "Accessories"),
        ("usb-c hub", "Accessories"),
        ("gaming monitor 144Hz", "Monitors"),
    ],
    "Audio": [
        ("phone charger fast charging cable", "Accessories"),
        ("power bank", "Accessories"),
    ],
    "Monitors": [
        ("usb-c hub", "Accessories"),
        ("mechanical keyboard", "Accessories"),
        ("wireless mouse", "Accessories"),
    ],
    "Footwear": [
        ("running shoes", "Footwear"),
        ("track pants", "Clothing"),
    ],
    "Eyewear": [
        ("sunglasses", "Eyewear"),
    ],
}


async def _find_complements(category: str, *, per_query: int = 2) -> list[dict]:
    """Vector-search for items that naturally pair with the just-decided category."""
    plan = COMPLEMENT_QUERIES.get(category, [])
    slugs: list[str] = []
    seen: set[str] = set()
    for query, cat_filter in plan:
        hits = await get_vector().search(query, top_k=per_query, category=cat_filter)
        for h in hits:
            if h["slug"] in seen:
                continue
            seen.add(h["slug"])
            slugs.append(h["slug"])
    if not slugs:
        return []
    return await get_product_service().get_many(slugs)


def _format_catalog(products: list[dict]) -> str:
    if not products:
        return "(no matching products)"
    lines = []
    for p in products[:8]:
        lines.append(
            f"- {p['title']} | {p.get('brand','')} | {p['category']} | ₹{p['price']:.0f} | rating {p.get('rating', 0)} | tags: {', '.join(p.get('tags', [])[:5])}"
        )
    return "\n".join(lines)


class AIOrchestrator:
    async def handle_turn(
        self,
        *,
        user_id: str,
        session_id: str,
        user_message: str,
    ) -> dict:
        convo_svc = get_conversation_service()
        await convo_svc.get_or_create(user_id, session_id)
        await convo_svc.append_message(user_id, session_id, "user", user_message)

        history_doc = await get_conversation_service().history_messages(user_id, session_id, limit=10)
        history = _format_history(history_doc)

        # 1) Intent extraction (JSON mode).
        intent_messages = [
            {"role": "system", "content": INTENT_PROMPT},
            *history[-6:],
            {"role": "user", "content": user_message},
        ]
        raw = await get_chat_llm().chat(intent_messages, temperature=0.1, json_mode=True)
        intent = _parse_json_object(raw)

        # 2) Decide what to search for. Combine LLM signal with deterministic
        # keyword hints — a 3B model often forgets to set category for short
        # follow-ups like "yeah iPhone I want", and pure vector search across
        # 2k+ products then returns category-mismatched noise.
        last_assistant = next(
            (m["content"] for m in reversed(history_doc) if m.get("role") == "assistant"),
            "",
        )
        # Keyword hinter is deterministic; prefer it over the LLM's guess.
        # Only fall back to the LLM's category if the hinter found nothing.
        kw_category = hint_category(user_message, last_assistant)
        hinted_category = kw_category or intent.get("category")
        hinted_brand = hint_brand(user_message, last_assistant)

        # Search query: if LLM gave something solid use it, otherwise build from
        # user message + last assistant context so short replies still retrieve well.
        llm_q = (intent.get("search_query") or "").strip()
        if len(llm_q) >= 6:
            search_q = llm_q
        else:
            search_q = (user_message + " " + last_assistant).strip()

        is_search_intent = intent.get("intent") in {"product_search", "complementary", "compare"}
        purchase_intent = bool(intent.get("purchase_intent"))
        complement_for = intent.get("complement_for")
        # A clear category/brand hint from keywords almost always means the user
        # wants products — override the LLM's intent label, since small models often
        # mislabel short follow-ups as "clarify" or "smalltalk".
        if hinted_category:
            is_search_intent = True
        # Purchase intent → also a "search" path, but for complementary items.
        if purchase_intent:
            is_search_intent = True

        products: list[dict] = []
        if is_search_intent and search_q:
            price_range: Optional[tuple[float, float]] = None
            if intent.get("min_price") or intent.get("max_price"):
                price_range = (
                    float(intent.get("min_price") or 0),
                    float(intent.get("max_price") or 1_000_000_000),
                )
            MIN_RELEVANCE = 0.60  # cosine; real matches score 0.65+

            # Purchase-intent path: pivot to accessories for the just-decided category.
            if purchase_intent and (complement_for or hinted_category):
                base_cat = complement_for or hinted_category
                products = await _find_complements(base_cat)
            else:
                hits = await get_vector().search(
                    search_q,
                    top_k=8,
                    category=hinted_category,
                    brand=hinted_brand,
                    price_range=price_range,
                )
                # Fallback 1: drop brand.
                if not hits and hinted_brand:
                    hits = await get_vector().search(
                        search_q, top_k=8, category=hinted_category, price_range=price_range
                    )
                # Fallback 2: soft budget relaxation up to 50% — surface items just
                # over budget so a "15k phone" query doesn't silently return nothing,
                # but also doesn't silently show 2-3x-over-budget items.
                if not hits and price_range:
                    relaxed = (price_range[0], price_range[1] * 1.5)
                    hits = await get_vector().search(
                        search_q, top_k=8, category=hinted_category, price_range=relaxed
                    )
                    if hits:
                        intent["budget_relaxed"] = True
                        intent["budget_relaxed_to"] = int(relaxed[1])

                # Relevance gate (only when no category hint — otherwise trust filter).
                if not hinted_category:
                    hits = [h for h in hits if h.get("score", 0) >= MIN_RELEVANCE]

                products = await get_product_service().get_many([h["slug"] for h in hits])

            # Persist hinted category back so downstream UI / reply prompt knows.
            if hinted_category and not intent.get("category"):
                intent["category"] = hinted_category

        # 3) Persist preferences inferred from this turn.
        new_prefs = intent.get("preferences") or {}
        if new_prefs:
            doc = await get_conversation_service().get_or_create(user_id, session_id)
            merged = _merge_preferences(doc.get("extracted_preferences", {}), new_prefs)
            await get_conversation_service().update_preferences(user_id, session_id, merged)
        else:
            doc = await get_conversation_service().get_or_create(user_id, session_id)
            merged = doc.get("extracted_preferences", {})

        # 4) Generate grounded reply.
        catalog_block = _format_catalog(products)
        prefs_block = json.dumps(merged) if merged else "(none yet)"
        # If the user clearly searched for products but we have zero matches,
        # use a stricter prompt that forbids inventing items.
        had_search_intent = is_search_intent and search_q
        active_system_prompt = (
            NO_RESULTS_PROMPT if (had_search_intent and not products) else SYSTEM_PROMPT
        )
        reply_messages = [
            {"role": "system", "content": active_system_prompt},
            {
                "role": "system",
                "content": (
                    f"USER_PREFERENCES: {prefs_block}\n"
                    f"CATALOG_RESULTS:\n{catalog_block}\n\n"
                    "If CATALOG_RESULTS is non-empty, recommend 2-3 of them by name. "
                    + ("Note: nothing was found at the user's exact budget — these are slightly over. Mention this honestly. "
                       if intent.get("budget_relaxed") else "")
                    + ("The user just decided to buy a product, so these results are complementary accessories that pair well — frame them that way, e.g. \"Nice choice! Here are some things that'd go great with it…\". "
                       if intent.get("purchase_intent") else "")
                    + "If a useful follow-up question is suggested below, ask it naturally."
                ),
            },
            *history,
            {"role": "user", "content": user_message},
        ]
        if intent.get("follow_up_needed") and intent.get("follow_up_question"):
            reply_messages.append(
                {
                    "role": "system",
                    "content": f"SUGGESTED_FOLLOW_UP: {intent['follow_up_question']}",
                }
            )

        reply_text = await get_chat_llm().chat(reply_messages, temperature=0.5)

        # 5) Persist assistant message + return.
        product_slugs = [p["slug"] for p in products]
        await convo_svc.append_message(
            user_id, session_id, "assistant", reply_text, products=product_slugs
        )

        return {
            "reply": reply_text,
            "products": products,
            "follow_up": intent.get("follow_up_question") or None,
            "preferences": merged,
        }


_orch: AIOrchestrator | None = None


def get_orchestrator() -> AIOrchestrator:
    global _orch
    if _orch is None:
        _orch = AIOrchestrator()
    return _orch
