"""MCP tool interceptor that fronts Portal MCP servers with per-call sessions.

The MOA auth headers (Moa-Token, Moa-Project, MS-Biz) are user/session-specific
and must be bound at session-creation time for HTTP/SSE transports — modifying
``MCPToolCallRequest.headers`` is a no-op because DeerFlow's persistent-session
handler does not forward headers to ``ClientSession.call_tool()``.

Strategy
--------
This interceptor short-circuits the pooled session for Portal MCP servers.
For every Portal tool call it:

1. Reads ``moa_token`` / ``moa_project`` / ``ms_biz`` from
   ``get_config()['metadata']`` (stamped per-request by ``PortalAuthMiddleware``).
2. Opens a fresh ``ClientSession`` with those headers via
   ``langchain_mcp_adapters.sessions.create_session``.
3. Returns the ``CallToolResult`` directly, never invoking ``handler(request)``.

Trade-off vs. persistent pool: one extra MCP handshake per Portal call. In
exchange, zero upstream DeerFlow modifications are required, per-request token
rotation works automatically, and stale-session reuse across users/threads is
impossible by construction.

Registered via ``mcpInterceptors`` in ``extensions_config.json``.
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.config import get_config

logger = logging.getLogger(__name__)

# MCP server names whose calls must go through the Portal auth path.
_PORTAL_SERVER_NAMES = frozenset(
    {
        "mirrorsphere-portal",
        "mirrorsphere-portal-sse",
    }
)

# Mapping: LangGraph metadata key -> outbound HTTP header name.
_HEADER_MAP = {
    "moa_token": "Moa-Token",
    "moa_project": "Moa-Project",
    "ms_biz": "MS-Biz",
}


def _load_portal_connections() -> dict[str, dict[str, Any]]:
    """Snapshot connection params for Portal MCP servers at interceptor build time.

    Reuses DeerFlow's own loader so URL/env-var resolution stays identical to
    the pooled path; we only swap headers per-call.
    """
    try:
        from deerflow.config.extensions_config import ExtensionsConfig
        from deerflow.mcp.client import build_server_params
    except ImportError:
        logger.warning("DeerFlow modules not importable; Portal MCP interceptor disabled")
        return {}

    try:
        extensions_config = ExtensionsConfig.from_file()
    except Exception:
        logger.warning("Failed to load extensions config; Portal MCP interceptor disabled", exc_info=True)
        return {}

    enabled = extensions_config.get_enabled_mcp_servers()
    connections: dict[str, dict[str, Any]] = {}
    for name in _PORTAL_SERVER_NAMES:
        cfg = enabled.get(name)
        if cfg is None:
            continue
        try:
            connections[name] = build_server_params(name, cfg)
        except Exception:
            logger.warning("Failed to build connection for %s; skipping", name, exc_info=True)
    return connections


def build_portal_headers_interceptor() -> Any:
    """Builder for ``mcpInterceptors`` registration.

    Returns an async callable compatible with
    ``MultiServerMCPClient.tool_interceptors``.
    """
    portal_connections = _load_portal_connections()
    if not portal_connections:
        logger.info("portal_headers_interceptor: no Portal MCP servers enabled; interceptor is a no-op")

    async def portal_headers_interceptor(request: Any, handler: Any) -> Any:
        server_name = getattr(request, "server_name", None)
        if server_name not in portal_connections:
            return await handler(request)

        try:
            config = get_config()
        except RuntimeError:
            # Outside a LangGraph execution context (e.g. tool discovery probes).
            return await handler(request)

        metadata = (config.get("metadata") if isinstance(config, dict) else None) or {}

        headers: dict[str, str] = {}
        for meta_key, header_name in _HEADER_MAP.items():
            value = metadata.get(meta_key)
            if value:
                headers[header_name] = str(value)

        if not headers:
            logger.warning(
                "portal_headers_interceptor: no Portal auth metadata for %s; falling back to pooled session",
                server_name,
            )
            return await handler(request)

        connection = dict(portal_connections[server_name])
        merged_headers = dict(connection.get("headers") or {})
        merged_headers.update(headers)
        connection["headers"] = merged_headers

        from langchain_mcp_adapters.sessions import create_session

        logger.debug(
            "portal_headers_interceptor: opening fresh session for %s (header keys=%s)",
            server_name,
            sorted(headers.keys()),
        )
        async with create_session(connection) as session:
            await session.initialize()
            return await session.call_tool(request.name, request.args)

    return portal_headers_interceptor
