from __future__ import annotations

from typing import Any


def diff_cases(old: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, Any]:
    if not old:
        return {"added": _all_case_ids(new), "removed": [], "changed": [], "summary": "no previous baseline"}

    old_map = _scenario_map(old)
    new_map = _scenario_map(new)

    added = sorted(set(new_map) - set(old_map))
    removed = sorted(set(old_map) - set(new_map))
    changed = sorted([cid for cid in (set(new_map) & set(old_map)) if new_map[cid] != old_map[cid]])

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "summary": f"added={len(added)} removed={len(removed)} changed={len(changed)}",
    }


def render_diff_md(diff: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Diff Summary")
    lines.append("")
    lines.append(f"- {diff.get('summary', '')}")
    lines.append("")
    for key, title in (("added", "Added"), ("removed", "Removed"), ("changed", "Changed")):
        items = diff.get(key, [])
        lines.append(f"## {title} ({len(items)})")
        for cid in items[:200]:
            lines.append(f"- {cid}")
        if len(items) > 200:
            lines.append(f"- ... and {len(items) - 200} more")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _scenario_map(cases: dict[str, Any]) -> dict[str, Any]:
    m: dict[str, Any] = {}
    for mod in cases.get("modules", []):
        for s in mod.get("scenarios", []):
            sid = s.get("id")
            if sid:
                m[sid] = s
    return m


def _all_case_ids(cases: dict[str, Any]) -> list[str]:
    return sorted(_scenario_map(cases).keys())

