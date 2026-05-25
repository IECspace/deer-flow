"""Configuration for Portal authentication integration."""

from __future__ import annotations

import os


PORTAL_AUTH_ENABLED: bool = os.getenv("PORTAL_AUTH_ENABLED", "false").lower() in ("true", "1", "yes")

PORTAL_API_URL: str = os.getenv("PORTAL_API_URL", "http://localhost:8089")

PORTAL_USER_INFO_PATH: str = os.getenv("PORTAL_USER_INFO_PATH", "/user/info")

# Cookie names as set by Portal frontend
PORTAL_COOKIE_MOA_TOKEN: str = "moa_token"
PORTAL_COOKIE_MOA_PROJECT: str = "moa_project"
PORTAL_COOKIE_MS_BIZ: str = "ms_biz"

# Cache validated tokens in memory to avoid calling Portal API on every request
PORTAL_TOKEN_CACHE_TTL_SECONDS: int = int(os.getenv("PORTAL_TOKEN_CACHE_TTL", "300"))
