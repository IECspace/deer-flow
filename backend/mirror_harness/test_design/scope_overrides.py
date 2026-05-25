from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .scope import ScopeConfig, scope_from_profile


@dataclass(frozen=True)
class ScopeOverrides:
    include_categories: set[str] | None = None
    exclude_categories: set[str] | None = None
    include_nfr: bool | None = None
    include_permission: bool | None = None
    include_boundary: bool | None = None
    max_cases_per_requirement: int | None = None


def load_scope_overrides(path: Path) -> ScopeOverrides:
    raw = _load_yaml_or_json(path)
    if not isinstance(raw, dict):
        return ScopeOverrides()
    inc = raw.get("include_categories")
    exc = raw.get("exclude_categories")
    return ScopeOverrides(
        include_categories=set(inc) if isinstance(inc, list) else None,
        exclude_categories=set(exc) if isinstance(exc, list) else None,
        include_nfr=_opt_bool(raw.get("include_nfr")),
        include_permission=_opt_bool(raw.get("include_permission")),
        include_boundary=_opt_bool(raw.get("include_boundary")),
        max_cases_per_requirement=_opt_int(raw.get("max_cases_per_requirement")),
    )


def apply_scope_overrides(scope: ScopeConfig, overrides: ScopeOverrides) -> ScopeConfig:
    return ScopeConfig(
        profile=scope.profile,
        include_nfr=overrides.include_nfr if overrides.include_nfr is not None else scope.include_nfr,
        include_permission=overrides.include_permission if overrides.include_permission is not None else scope.include_permission,
        include_boundary=overrides.include_boundary if overrides.include_boundary is not None else scope.include_boundary,
        max_cases_per_requirement=overrides.max_cases_per_requirement if overrides.max_cases_per_requirement is not None else scope.max_cases_per_requirement,
    )


def default_scope_overrides_template() -> dict[str, Any]:
    return {
        "include_categories": ["functional", "nonfunctional"],
        "exclude_categories": ["rollout", "risk", "analytics", "data"],
        "include_nfr": True,
        "include_permission": True,
        "include_boundary": True,
        "max_cases_per_requirement": 4,
    }


def resolve_scope(profile: str, scope_overrides_path: Path | None) -> tuple[ScopeConfig, set[str] | None, set[str] | None]:
    scope = scope_from_profile(profile)  # type: ignore[arg-type]
    include_categories: set[str] | None = None
    exclude_categories: set[str] | None = None
    if scope_overrides_path and scope_overrides_path.exists():
        ov = load_scope_overrides(scope_overrides_path)
        scope = apply_scope_overrides(scope, ov)
        include_categories = ov.include_categories
        exclude_categories = ov.exclude_categories
    return scope, include_categories, exclude_categories


def _opt_bool(val: Any) -> bool | None:
    if isinstance(val, bool):
        return val
    return None


def _opt_int(val: Any) -> int | None:
    if isinstance(val, int):
        return val
    return None


def _load_yaml_or_json(path: Path) -> Any:
    content = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(content) or {}
    except Exception:
        import json

        try:
            return json.loads(content)
        except Exception:
            return {}

