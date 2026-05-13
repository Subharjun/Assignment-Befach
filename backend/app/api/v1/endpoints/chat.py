from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user_id
from app.schemas.chat import ChatTurnIn, ChatTurnOut, ConversationOut
from app.services.ai_orchestrator import get_orchestrator
from app.services.conversation_service import get_conversation_service
from app.services.product_service import get_product_service

router = APIRouter(prefix="/chat", tags=["chat"])


class SessionSummary(BaseModel):
    session_id: str
    preview: str
    updated_at: Optional[datetime] = None


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(user_id: str = Depends(get_current_user_id)):
    return await get_conversation_service().list_sessions(user_id, limit=30)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str = Depends(get_current_user_id)):
    removed = await get_conversation_service().delete_session(user_id, session_id)
    return {"deleted": removed}


@router.post("", response_model=ChatTurnOut)
async def chat_turn(body: ChatTurnIn, user_id: str = Depends(get_current_user_id)):
    result = await get_orchestrator().handle_turn(
        user_id=user_id, session_id=body.session_id, user_message=body.message
    )
    return {
        "session_id": body.session_id,
        "reply": result["reply"],
        "products": result["products"],
        "follow_up": result["follow_up"],
        "preferences": result["preferences"],
    }


@router.get("/{session_id}", response_model=ConversationOut)
async def get_conversation(session_id: str, user_id: str = Depends(get_current_user_id)):
    convo = await get_conversation_service().get_or_create(user_id, session_id)
    raw_messages = convo.get("messages", [])

    # Collect every product slug referenced across the conversation and resolve
    # them in one round-trip so the resumed chat can render product cards
    # (the stored messages only hold slugs, not full product objects).
    all_slugs: list[str] = []
    for m in raw_messages:
        for s in m.get("products", []) or []:
            if s not in all_slugs:
                all_slugs.append(s)
    products_by_slug: dict[str, dict] = {}
    if all_slugs:
        resolved = await get_product_service().get_many(all_slugs)
        products_by_slug = {p["slug"]: p for p in resolved}

    messages_out = []
    for m in raw_messages:
        full = [products_by_slug[s] for s in (m.get("products") or []) if s in products_by_slug]
        messages_out.append(
            {"role": m["role"], "content": m["content"], "products": full}
        )

    return {
        "session_id": session_id,
        "messages": messages_out,
        "extracted_preferences": convo.get("extracted_preferences", {}),
    }
