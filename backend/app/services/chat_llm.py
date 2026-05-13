"""Chat LLM abstraction. Uses Groq if GROQ_API_KEY is set, else Ollama.

Embeddings always use Ollama (see ollama_service). This split lets us run a
strong hosted model for reasoning while keeping vector embeddings local +
free.
"""
from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from app.core.config import get_settings
from app.services.ollama_service import get_ollama


class GroqChatLLM:
    """Thin OpenAI-compatible Groq client."""

    BASE = "https://api.groq.com/openai/v1"

    def __init__(self) -> None:
        s = get_settings()
        self.api_key = s.GROQ_API_KEY
        self.model = s.GROQ_CHAT_MODEL

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.4,
        json_mode: bool = False,
    ) -> str:
        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.BASE}/chat/completions", headers=self._headers(), json=payload
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(
        self, messages: list[dict], *, temperature: float = 0.4
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.BASE}/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as r:
                r.raise_for_status()
                async for raw in r.aiter_lines():
                    if not raw or not raw.startswith("data: "):
                        continue
                    body = raw[6:]
                    if body == "[DONE]":
                        return
                    try:
                        chunk = json.loads(body)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk["choices"][0].get("delta", {}).get("content")
                    if delta:
                        yield delta


class OllamaChatAdapter:
    """Adapter so OllamaService implements the same chat interface."""

    async def chat(self, messages, *, temperature=0.4, json_mode=False) -> str:
        return await get_ollama().chat(messages, temperature=temperature, json_mode=json_mode)

    async def chat_stream(self, messages, *, temperature=0.4):
        async for chunk in get_ollama().chat_stream(messages, temperature=temperature):
            yield chunk


_chat_llm: GroqChatLLM | OllamaChatAdapter | None = None


def get_chat_llm() -> GroqChatLLM | OllamaChatAdapter:
    global _chat_llm
    if _chat_llm is None:
        if get_settings().GROQ_API_KEY:
            _chat_llm = GroqChatLLM()
        else:
            _chat_llm = OllamaChatAdapter()
    return _chat_llm
