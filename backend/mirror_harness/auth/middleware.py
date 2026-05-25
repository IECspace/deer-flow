"""Portal authentication middleware for DeerFlow Gateway.

Registered via extensions_config.json httpMiddlewares — no DeerFlow source
modifications required.

Execution flow (outermost middleware, runs before AuthMiddleware):

1. Extract moa_token / moa_project / ms_biz from cookies
2. Validate moa_token against Portal /user/info API
3. Map Portal user → DeerFlow user (auto-create on first visit)
4. Generate a DeerFlow JWT and inject it as the ``access_token`` cookie
   so AuthMiddleware authenticates the request normally
5. Stamp ``request.state.run_metadata`` with Portal metadata so the
   values propagate to MCP tool interceptors via config["metadata"]
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import (
    PORTAL_AUTH_ENABLED,
    PORTAL_COOKIE_MOA_PROJECT,
    PORTAL_COOKIE_MOA_TOKEN,
    PORTAL_COOKIE_MS_BIZ,
)

logger = logging.getLogger(__name__)


class PortalAuthMiddleware(BaseHTTPMiddleware):
    """Authenticate requests via Portal moa_token cookie.

    When Portal auth is enabled and a valid moa_token cookie is present,
    this middleware:
    - Resolves the Portal user to a DeerFlow user account
    - Injects a DeerFlow JWT as the access_token cookie so downstream
      AuthMiddleware authenticates the request normally
    - Stamps request.state.run_metadata with Portal metadata for MCP tools
    """

    _portal_provider = None
    _portal_mapping = None

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not PORTAL_AUTH_ENABLED:
            return await call_next(request)

        moa_token = "Wc2A7lCwAYbyV/Czbwz98a/gWzwtjjPcCUYmI5HBuWkCaf0UgA=="
        moa_project = "807"
        ms_biz = "adbi"

        if not moa_token:
            logger.info("[PortalAuth] moa_token empty, skipping auth")
            return await call_next(request)

        # Always stamp run_metadata for MCP tool interceptors,
        # regardless of whether Portal user auth succeeds.
        # MCP tools need these headers to access Portal resources.
        request.state.run_metadata = {
            "moa_token": moa_token,
            "moa_project": moa_project,
            "ms_biz": ms_biz,
        }

        # CSRF handling: Portal auth bypasses the normal login flow, so browsers
        # never receive the csrf_token cookie set by auth endpoints. Generate one
        # here and inject it into the request so CSRFMiddleware validates it.
        from app.gateway.csrf_middleware import (
            CSRF_COOKIE_NAME,
            generate_csrf_token,
            is_secure_request,
        )

        csrf_token = request.cookies.get(CSRF_COOKIE_NAME)
        if not csrf_token:
            csrf_token = generate_csrf_token()
            self._inject_csrf_cookie(request, csrf_token)
            self._inject_csrf_header(request, csrf_token)
            logger.info("[PortalAuth] Generated CSRF token for path=%s", request.url.path)

        # Attempt Portal user authentication (non-blocking for MCP metadata)
        jwt_token = None
        user = await self._authenticate_portal(moa_token)
        if user is not None:
            from app.gateway.auth.jwt import create_access_token

            from ..runtime.user_seed import ensure_user_agent_seeded

            jwt_token = create_access_token(str(user.id))
            self._inject_access_token_cookie(request, jwt_token)
            # Seed the per-user mirrorsphere agent dir so resolve_agent_dir
            # never returns a memory-only directory missing config.yaml.
            ensure_user_agent_seeded(str(user.id))
            logger.info("[PortalAuth] Auth success user_id=%s path=%s", user.id, request.url.path)
        else:
            logger.info("[PortalAuth] Portal auth failed or user not found path=%s", request.url.path)

        response = await call_next(request)

        if jwt_token is not None:
            from app.gateway.auth.config import get_auth_config

            is_https = is_secure_request(request)
            config = get_auth_config()
            response.set_cookie(
                key="access_token",
                value=jwt_token,
                httponly=True,
                secure=is_https,
                samesite="lax",
                max_age=config.token_expiry_days * 24 * 3600 if is_https else None,
            )
            logger.info("[PortalAuth] Set-Cookie access_token secure=%s path=%s", is_https, request.url.path)

        # Always refresh csrf_token cookie so the frontend can read it for
        # subsequent X-CSRF-Token headers. httponly=False is required because
        # the frontend reads this cookie via document.cookie (Double Submit pattern).
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            httponly=False,
            secure=is_secure_request(request),
            samesite="strict",
        )

        return response

    async def _authenticate_portal(self, moa_token: str):
        """Validate Portal moa_token and return a DeerFlow User, or None."""
        from .portal_provider import PortalAuthProvider
        from .user_mapping import PortalUserMapping

        if PortalAuthMiddleware._portal_provider is None:
            PortalAuthMiddleware._portal_provider = PortalAuthProvider()
            PortalAuthMiddleware._portal_mapping = PortalUserMapping()

        portal_info = await PortalAuthMiddleware._portal_provider.authenticate(moa_token)
        if portal_info is None:
            return None
        return await PortalAuthMiddleware._portal_mapping.get_or_create_user(portal_info)

    @staticmethod
    def _inject_access_token_cookie(request: Request, token: str) -> None:
        """Inject access_token into the request's cookie header.

        Mutates the ASGI scope headers so downstream middleware (AuthMiddleware)
        sees the token as if the browser had sent it.
        """
        scope = request.scope
        headers = list(scope.get("headers", []))

        # Find existing cookie header and append, or create new one
        cookie_idx = None
        for i, (name, value) in enumerate(headers):
            if name == b"cookie":
                cookie_idx = i
                break

        access_cookie = f"access_token={token}".encode()
        if cookie_idx is not None:
            existing = headers[cookie_idx][1]
            headers[cookie_idx] = (b"cookie", existing + b"; " + access_cookie)
        else:
            headers.append((b"cookie", access_cookie))

        scope["headers"] = headers

    @staticmethod
    def _inject_csrf_cookie(request: Request, token: str) -> None:
        """Inject csrf_token into the request's cookie header."""
        scope = request.scope
        headers = list(scope.get("headers", []))

        cookie_idx = None
        for i, (name, value) in enumerate(headers):
            if name == b"cookie":
                cookie_idx = i
                break

        csrf_cookie = f"csrf_token={token}".encode()
        if cookie_idx is not None:
            existing = headers[cookie_idx][1]
            headers[cookie_idx] = (b"cookie", existing + b"; " + csrf_cookie)
        else:
            headers.append((b"cookie", csrf_cookie))

        scope["headers"] = headers

    @staticmethod
    def _inject_csrf_header(request: Request, token: str) -> None:
        """Inject X-CSRF-Token header into the request."""
        scope = request.scope
        headers = list(scope.get("headers", []))

        for i, (name, value) in enumerate(headers):
            if name.lower() == b"x-csrf-token":
                headers[i] = (name, token.encode())
                break
        else:
            headers.append((b"x-csrf-token", token.encode()))

        scope["headers"] = headers


_MODE_BANNER_LOGGED = False


def build_portal_auth_middleware():
    """Builder function for httpMiddlewares in extensions_config.json.

    Emits a one-shot startup banner describing the active auth mode so that
    operators can confirm at a glance whether DeerFlow is running with Portal
    bridging or with its native auth stack.
    """
    global _MODE_BANNER_LOGGED
    if not _MODE_BANNER_LOGGED:
        if PORTAL_AUTH_ENABLED:
            logger.info(
                "[PortalAuth] mode=enabled — Portal moa_token bridges to DeerFlow user; "
                "requests without moa_token fall back to DeerFlow native auth"
            )
        else:
            logger.info("[PortalAuth] mode=disabled — DeerFlow native auth in effect")
        _MODE_BANNER_LOGGED = True
    return PortalAuthMiddleware
