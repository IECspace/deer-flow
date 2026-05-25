from __future__ import annotations

from pathlib import Path

from .models import TestDesignModel
from .utils import ensure_dir


def render_all(model: TestDesignModel, out_dir: Path) -> dict[str, Path]:
    ensure_dir(out_dir)
    paths: dict[str, Path] = {}

    summary_path = out_dir / "test-design-summary.md"
    summary_path.write_text(render_summary(model), encoding="utf-8")
    paths["test_design_summary"] = summary_path

    test_points_path = out_dir / "test-points.md"
    test_points_path.write_text(render_test_points(model), encoding="utf-8")
    paths["test_points"] = test_points_path

    cases_path = out_dir / "test-cases.md"
    cases_path.write_text(render_test_cases(model), encoding="utf-8")
    paths["test_cases"] = cases_path

    mindmap_path = out_dir / "mindmap.mmd"
    mindmap_path.write_text(render_mindmap(model), encoding="utf-8")
    paths["mindmap"] = mindmap_path

    gaps_path = out_dir / "gaps.md"
    gaps_path.write_text(render_gaps(model), encoding="utf-8")
    paths["gaps"] = gaps_path

    return paths


def render_summary(model: TestDesignModel) -> str:
    prd = model.to_dict()["prd"]
    lines: list[str] = []
    lines.append(f"# Test Design Summary: {prd['title']}")
    lines.append("")
    lines.append(f"- PRD ID: {prd['id']}")
    if prd.get("version"):
        lines.append(f"- Version: {prd['version']}")
    if prd.get("source"):
        lines.append(f"- Source: {prd['source']}")
    lines.append("")
    lines.append("## Modules")
    for m in model.modules:
        lines.append(f"- {m.name} ({m.category}, {len(m.requirements)} items)")
    lines.append("")
    if model.assumptions:
        lines.append("## Confirmed Notes / Assumptions")
        for a in model.assumptions:
            lines.append(f"- {a}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_test_points(model: TestDesignModel) -> str:
    lines: list[str] = []
    lines.append("# Test Points")
    lines.append("")
    for m in model.modules:
        if m.category not in {"functional", "nonfunctional"}:
            continue
        lines.append(f"## {m.name}")
        for r in m.requirements:
            lines.append(f"- [{r.requirement_id}] {r.statement}")
            lines.append("  - 覆盖：正常流程 / 异常流程 / 边界 / 权限（按需）")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_test_cases(model: TestDesignModel) -> str:
    lines: list[str] = []
    lines.append("# Test Cases (Draft)")
    lines.append("")
    for m in model.modules:
        if m.category not in {"functional", "nonfunctional"}:
            continue
        lines.append(f"## Module: {m.name}")
        lines.append("")
        for s in m.scenarios:
            lines.append(f"### {s.name}")
            lines.append("")
            lines.append(f"- ID: `{s.scenario_id}`")
            lines.append(f"- Type: `{s.type}`")
            lines.append(f"- Priority: `{s.priority}`")
            if s.trace_requirement_ids:
                lines.append(f"- Trace: {', '.join(s.trace_requirement_ids)}")
            if s.tags:
                lines.append(f"- Tags: {', '.join(s.tags)}")
            lines.append("")
            if s.preconditions:
                lines.append("**Preconditions**")
                for p in s.preconditions:
                    lines.append(f"- {p}")
                lines.append("")
            lines.append("**Steps**")
            for idx, step in enumerate(s.steps, start=1):
                lines.append(f"{idx}. {step.action}")
                if step.data:
                    lines.append(f"   - Data: {step.data}")
                if step.expected:
                    lines.append(f"   - Expected: {step.expected}")
            lines.append("")
            if s.assertions:
                lines.append("**Assertions**")
                for a in s.assertions:
                    lines.append(f"- {a}")
                lines.append("")
            if s.risks:
                lines.append("**Risks / Open Questions**")
                for r in s.risks:
                    lines.append(f"- {r}")
                lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_mindmap(model: TestDesignModel) -> str:
    """Render a Mermaid diagram in left-to-right layout (LR).

    Mermaid mindmap syntax does not reliably support direction control across renderers,
    so we use `flowchart LR` as the default to guarantee left-to-right diagrams.
    """

    title = (model.title or "PRD").replace('"', "'").strip()[:80] or "PRD"

    lines: list[str] = []
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append("")

    root_id = "ROOT"
    lines.append(f'{root_id}["{title}"]')

    # Modules -> scenario types -> scenarios
    for mi, m in enumerate(model.modules, start=1):
        if m.category not in {"functional", "nonfunctional"}:
            continue
        mod_id = f"M{mi}"
        mod_label = (m.name or f"Module {mi}").replace('"', "'").strip()[:80]
        lines.append(f'{root_id} --> {mod_id}["{mod_label}"]')

        by_type: dict[str, list[str]] = {}
        for s in m.scenarios:
            by_type.setdefault(s.type, []).append(s.name)

        for ti, (t, names) in enumerate(sorted(by_type.items(), key=lambda x: x[0]), start=1):
            type_id = f"{mod_id}_T{ti}"
            lines.append(f'{mod_id} --> {type_id}["{t}"]')
            for si, n in enumerate(names[:25], start=1):
                scen_id = f"{type_id}_S{si}"
                label = (n or "Scenario").replace('"', "'").strip()[:90]
                lines.append(f'{type_id} --> {scen_id}["{label}"]')

    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def render_gaps(model: TestDesignModel) -> str:
    lines: list[str] = []
    lines.append("# Test Design Gaps (Need Confirmation)")
    lines.append("")
    if not model.gaps:
        lines.append("No gaps detected. If anything is still uncertain, add it explicitly before finalizing cases.")
        lines.append("")
        return "\n".join(lines)
    for g in model.gaps:
        lines.append(f"## {g.question_id}")
        lines.append(f"- Question: {g.question}")
        lines.append(f"- Why it matters: {g.why_it_matters}")
        lines.append(f"- Suggested owner: {g.suggested_owner}")
        lines.append("")
    lines.append("## How to answer")
    lines.append("- Fill `answers.json` (a dict keyed by question_id) and rerun generation.")
    lines.append("")
    return "\n".join(lines)


def _safe_label(text: str) -> str:
    cleaned = "".join(ch for ch in text if ch.isalnum() or ch in {"_", "-", " "}).strip()
    cleaned = cleaned.replace(" ", "_")
    return cleaned[:60] or "Item"

