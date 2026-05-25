"""MCP stdio server exposing the test_design pipeline as tools.

Usage:
    python3 -m mirror_harness.mcp.test_design_server

The server is registered in extensions_config.json as a stdio-type MCP server
and launched automatically by DeerFlow when the agent needs test-case generation.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from ..test_design.contracts import CASES_SCHEMA_VERSION
from ..test_design.diff import diff_cases as _diff_cases, render_diff_md
from ..test_design.models import TestDesignModel
from ..test_design.render import render_gaps, render_mindmap, render_summary, render_test_cases, render_test_points
from ..test_design.scope import ScopeConfig, scope_from_profile
from ..test_design.scope_overrides import resolve_scope
from ..test_design.scenario_builder import build_scenarios
from ..test_design.case_generator import generate_cases as _generate_cases

logger = logging.getLogger(__name__)

server = Server("mirrorsphere-test-design")


def _build_scope(profile: str, scope_overrides: dict[str, Any] | None) -> tuple[ScopeConfig, set[str] | None, set[str] | None]:
    if scope_overrides:
        include = set(scope_overrides["include_categories"]) if "include_categories" in scope_overrides else None
        exclude = set(scope_overrides["exclude_categories"]) if "exclude_categories" in scope_overrides else None
        scope = scope_from_profile(profile)
        return scope, include, exclude
    return resolve_scope(profile, scope_overrides_path=None)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="generate-cases",
            description="Generate test cases from a confirmed requirement model (JSON). Returns structured cases and a markdown summary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "requirement_model": {
                        "type": "object",
                        "description": "The confirmed requirement model JSON (output of PRD analysis phase, with prd/modules/gaps/assumptions keys).",
                    },
                    "profile": {
                        "type": "string",
                        "enum": ["minimal", "standard", "strict"],
                        "default": "standard",
                        "description": "Coverage profile: minimal (2 cases/req), standard (4), strict (6).",
                    },
                    "scope_overrides": {
                        "type": "object",
                        "description": "Optional scope overrides with include_categories/exclude_categories keys.",
                    },
                },
                "required": ["requirement_model"],
            },
        ),
        Tool(
            name="diff-cases",
            description="Compare two versions of generated cases and produce a diff summary.",
            inputSchema={
                "type": "object",
                "properties": {
                    "old_cases": {
                        "type": "object",
                        "description": "Previous cases JSON (nullable for first-time generation).",
                    },
                    "new_cases": {
                        "type": "object",
                        "description": "New cases JSON to compare against.",
                    },
                },
                "required": ["new_cases"],
            },
        ),
        Tool(
            name="render-cases",
            description="Render cases JSON into markdown documents (test cases, test points, mindmap, gaps).",
            inputSchema={
                "type": "object",
                "properties": {
                    "cases": {
                        "type": "object",
                        "description": "The cases JSON (output of generate-cases tool).",
                    },
                },
                "required": ["cases"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "generate-cases":
        return _handle_generate_cases(arguments)
    if name == "diff-cases":
        return _handle_diff_cases(arguments)
    if name == "render-cases":
        return _handle_render_cases(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


def _handle_generate_cases(args: dict[str, Any]) -> list[TextContent]:
    requirement_model = args["requirement_model"]
    profile = args.get("profile", "standard")
    scope_overrides = args.get("scope_overrides")

    model = TestDesignModel.from_dict(requirement_model)
    scope, include_cats, exclude_cats = _build_scope(profile, scope_overrides)
    model = build_scenarios(model, scope, include_categories=include_cats, exclude_categories=exclude_cats)
    model = _generate_cases(model, scope)

    cases = model.to_dict()
    cases["schema_version"] = CASES_SCHEMA_VERSION
    summary_md = render_test_cases(model)

    result = {"cases": cases, "summary_md": summary_md}
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _handle_diff_cases(args: dict[str, Any]) -> list[TextContent]:
    old_cases = args.get("old_cases")
    new_cases = args["new_cases"]

    diff = _diff_cases(old_cases, new_cases)
    diff_md = render_diff_md(diff)

    result = {"diff": diff, "diff_md": diff_md}
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


def _handle_render_cases(args: dict[str, Any]) -> list[TextContent]:
    cases = args["cases"]
    model = TestDesignModel.from_dict(cases)

    result = {
        "summary_md": render_summary(model),
        "test_cases_md": render_test_cases(model),
        "test_points_md": render_test_points(model),
        "mindmap_mmd": render_mindmap(model),
        "gaps_md": render_gaps(model),
    }
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        init_options = InitializationOptions(
            server_name="mirrorsphere-test-design",
            server_version="0.1.0",
            capabilities=server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
