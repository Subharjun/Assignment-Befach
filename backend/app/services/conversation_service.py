from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.db.mongodb import get_db


class ConversationService:
    async def get_or_create(self, user_id: str, session_id: str) -> dict:
        db = get_db()
        doc = await db.conversations.find_one({"user_id": user_id, "session_id": session_id})
        if doc:
            return doc
        doc = {
            "user_id": user_id,
            "session_id": session_id,
            "messages": [],
            "extracted_preferences": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await db.conversations.insert_one(doc)
        return doc

    async def append_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        products: Optional[list[str]] = None,
    ) -> None:
        await get_db().conversations.update_one(
            {"user_id": user_id, "session_id": session_id},
            {
                "$push": {
                    "messages": {
                        "role": role,
                        "content": content,
                        "products": products or [],
                        "created_at": datetime.utcnow(),
                    }
                },
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

    async def delete_session(self, user_id: str, session_id: str) -> bool:
        """Permanently delete a conversation. Returns True if a doc was removed."""
        res = await get_db().conversations.delete_one(
            {"user_id": user_id, "session_id": session_id}
        )
        return res.deleted_count > 0

    async def update_preferences(self, user_id: str, session_id: str, prefs: dict) -> None:
        if not prefs:
            return
        update = {f"extracted_preferences.{k}": v for k, v in prefs.items()}
        update["updated_at"] = datetime.utcnow()
        await get_db().conversations.update_one(
            {"user_id": user_id, "session_id": session_id},
            {"$set": update},
        )

    async def list_sessions(self, user_id: str, limit: int = 30) -> list[dict]:
        """List the user's conversations, newest first, with a short preview."""
        cursor = (
            get_db()
            .conversations.find(
                {"user_id": user_id},
                {"session_id": 1, "messages": {"$slice": 1}, "updated_at": 1, "created_at": 1},
            )
            .sort("updated_at", -1)
            .limit(limit)
        )
        out: list[dict] = []
        async for d in cursor:
            first_user = next(
                (m for m in d.get("messages", []) if m.get("role") == "user"),
                None,
            )
            preview = (first_user or {}).get("content", "")[:80] if first_user else ""
            out.append(
                {
                    "session_id": d["session_id"],
                    "preview": preview or "(empty conversation)",
                    "updated_at": d.get("updated_at"),
                }
            )
        return out

    async def history_messages(self, user_id: str, session_id: str, limit: int = 12) -> list[dict]:
        doc = await get_db().conversations.find_one(
            {"user_id": user_id, "session_id": session_id},
            {"messages": {"$slice": -limit}, "extracted_preferences": 1},
        )
        if not doc:
            return []
        return doc.get("messages", [])


_svc: ConversationService | None = None


def get_conversation_service() -> ConversationService:
    global _svc
    if _svc is None:
        _svc = ConversationService()
    return _svc
