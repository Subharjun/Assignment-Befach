"""Clerk JWT verification with JWKS caching.

In dev, if CLERK_JWKS_URL is unset, falls back to a permissive mode that
trusts the bearer token. We try to decode it as an unverified JWT and use
its `sub` (Clerk user id) — that stays stable across token rotation. If
the bearer is not a JWT, the raw string is used as the user id.
"""
from __future__ import annotations

import time
from typing import Optional

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import jwt
from jose.exceptions import JWTError

from app.core.config import get_settings


def _stable_id_from_token(token: str) -> str:
    """Best-effort: extract Clerk's `sub` claim without signature verification.

    Clerk rotates the full JWT string but the `sub` claim stays stable for a
    given user. In dev mode (no JWKS configured) this gives us a consistent
    user id so a conversation saved in turn 1 is still findable in turn 2.
    """
    try:
        claims = jwt.get_unverified_claims(token)
        sub = claims.get("sub")
        if sub:
            return str(sub)
    except Exception:
        pass
    return token

_JWKS_CACHE: dict = {"keys": None, "fetched_at": 0.0}
_JWKS_TTL = 3600


async def _get_jwks() -> dict:
    settings = get_settings()
    now = time.time()
    if _JWKS_CACHE["keys"] and now - _JWKS_CACHE["fetched_at"] < _JWKS_TTL:
        return _JWKS_CACHE["keys"]
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(settings.CLERK_JWKS_URL)
        r.raise_for_status()
        _JWKS_CACHE["keys"] = r.json()
        _JWKS_CACHE["fetched_at"] = now
    return _JWKS_CACHE["keys"]


async def get_current_user_id(
    authorization: Optional[str] = Header(default=None),
) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()

    settings = get_settings()
    if not settings.CLERK_JWKS_URL:
        # Dev fallback: decode the JWT without verification, use stable `sub`.
        # NEVER enable in prod — set CLERK_JWKS_URL before deploying.
        return _stable_id_from_token(token)

    try:
        jwks = await _get_jwks()
        header = jwt.get_unverified_header(token)
        key = next((k for k in jwks.get("keys", []) if k["kid"] == header.get("kid")), None)
        if not key:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown key id")
        payload = jwt.decode(
            token,
            key,
            algorithms=[header.get("alg", "RS256")],
            issuer=settings.CLERK_JWT_ISSUER or None,
            options={"verify_aud": False},
        )
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No sub in token")
        return sub
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {e}")


async def get_optional_user_id(
    authorization: Optional[str] = Header(default=None),
) -> Optional[str]:
    if not authorization:
        return None
    try:
        return await get_current_user_id(authorization)
    except HTTPException:
        return None
