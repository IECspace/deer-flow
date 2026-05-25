"""Validate moa_token against Portal's /user/info API."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .config import (
    PORTAL_API_URL,
    PORTAL_TOKEN_CACHE_TTL_SECONDS,
    PORTAL_USER_INFO_PATH,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PortalUserInfo:
    uid: str
    name: str
    nick: str


class PortalAuthProvider:
    """Validates moa_token via Portal HTTP API with in-memory cache."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[PortalUserInfo, float]] = {}
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def authenticate(self, moa_token: str) -> PortalUserInfo | None:
        """Validate token and return user info, or None if invalid."""
        cached = self._cache.get(moa_token)
        if cached is not None:
            user_info, expires_at = cached
            if time.time() < expires_at:
                return user_info
            del self._cache[moa_token]

        user_info = await self._call_portal_api(moa_token)
        if user_info is not None:
            self._cache[moa_token] = (user_info, time.time() + PORTAL_TOKEN_CACHE_TTL_SECONDS)
        return user_info

    async def _call_portal_api(self, moa_token: str) -> PortalUserInfo | None:
        url = f"{PORTAL_API_URL}{PORTAL_USER_INFO_PATH}"
        try:
            client = await self._get_client()
            resp = await client.get(url, headers={"Moa-Token": moa_token})
            if resp.status_code != 200:
                logger.warning("Portal API returned %d for token validation", resp.status_code)
                return None
            data: dict[str, Any] = resp.json()
            if data.get("code") != 0:
                logger.warning("Portal API returned error code: %s", data.get("message"))
                return None
            user_data = data.get("data", {})
            uid = user_data.get("uid")
            if uid is None:
                logger.warning("Portal API response missing uid field")
                return None
            return PortalUserInfo(
                uid=str(uid),
                name=user_data.get("name", ""),
                nick=user_data.get("nick", ""),
            )
        except Exception:
            logger.exception("Failed to validate moa_token via Portal API")
            return None

    def invalidate(self, moa_token: str) -> None:
        self._cache.pop(moa_token, None)
