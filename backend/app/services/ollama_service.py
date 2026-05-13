"""Thin async client for Ollama's HTTP API."""
from __future__ import annotations

import json
from typing import AsyncIterator, Iterable

import httpx

from app.core.config import get_settings


class OllamaService:
    def __init__(self) -> None:
        s = get_settings()
        self.base = s.OLLAMA_BASE_URL.rstrip("/")
        self.chat_model = s.OLLAMA_CHAT_MODEL
        self.embed_model = s.OLLAMA_EMBED_MODEL

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self.base}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
            )
            r.raise_for_status()
            return r.json()["embedding"]

    async def embed_batch(self, texts: Iterable[str]) -> list[list[float]]:
        # Ollama embed endpoint is single-input; loop sequentially (fast enough at seed scale).
        out: list[list[float]] = []
        for t in texts:
            out.append(await self.embed(t))
        return out

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.4,
        json_mode: bool = False,
    ) -> str:
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_mode:
            payload["format"] = "json"
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{self.base}/api/chat", json=payload)
            r.raise_for_status()
            return r.json()["message"]["content"]

    async def chat_stream(
        self, messages: list[dict], *, temperature: float = 0.4
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{self.base}/api/chat", json=payload) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg = data.get("message", {}).get("content", "")
                    if msg:
                        yield msg
                    if data.get("done"):
                        break


_ollama: OllamaService | None = None


def get_ollama() -> OllamaService:
    global _ollama
    if _ollama is None:
        _ollama = OllamaService()
    return _ollama
