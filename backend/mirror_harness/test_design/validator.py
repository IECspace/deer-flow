from __future__ import annotations

from typing import Any

from .contracts import CASES_SCHEMA_VERSION, GAPS_SCHEMA_VERSION, RUN_MANIFEST_VERSION


def validate_cases(cases: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if cases.get("schema_version") != CASES_SCHEMA_VERSION:
        errors.append(f"cases.schema_version must be {CASES_SCHEMA_VERSION}")
    prd = cases.get("prd", {})
    if not isinstance(prd, dict) or not prd.get("id") or not prd.get("title"):
        errors.append("cases.prd.id and cases.prd.title are required")
    modules = cases.get("modules")
    if not isinstance(modules, list) or not modules:
        errors.append("cases.modules must be a non-empty list")
        return errors

    seen_case_ids: set[str] = set()
    for m in modules:
        if not isinstance(m, dict):
            errors.append("module must be object")
            continue
        if not m.get("id") or not m.get("name"):
            errors.append("module.id and module.name are required")
        if "category" not in m:
            errors.append("module.category is required")
        scenarios = m.get("scenarios", [])
        if not isinstance(scenarios, list):
            errors.append("module.scenarios must be list")
            continue
        for s in scenarios:
            if not isinstance(s, dict):
                errors.append("scenario must be object")
                continue
            sid = s.get("id")
            if not sid:
                errors.append("scenario.id is required")
                continue
            if sid in seen_case_ids:
                errors.append(f"duplicate scenario.id: {sid}")
            seen_case_ids.add(sid)
            if not s.get("name") or not s.get("type") or not s.get("priority"):
                errors.append(f"scenario fields missing: {sid}")
            steps = s.get("steps", [])
            if not isinstance(steps, list) or not steps:
                errors.append(f"scenario.steps must be non-empty list: {sid}")
            else:
                for step in steps:
                    if not isinstance(step, dict) or not step.get("action"):
                        errors.append(f"scenario.step.action required: {sid}")
                        break
            trace = s.get("trace_requirement_ids", [])
            if trace is not None and not isinstance(trace, list):
                errors.append(f"scenario.trace_requirement_ids must be list: {sid}")
    return errors


def validate_gaps(gaps: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if gaps.get("schema_version") != GAPS_SCHEMA_VERSION:
        errors.append(f"gaps.schema_version must be {GAPS_SCHEMA_VERSION}")
    items = gaps.get("gaps", [])
    if not isinstance(items, list):
        errors.append("gaps.gaps must be list")
        return errors
    for g in items:
        if not isinstance(g, dict):
            errors.append("gap item must be object")
            continue
        if not g.get("question_id") or not g.get("question") or not g.get("why_it_matters"):
            errors.append("gap.question_id/question/why_it_matters required")
    return errors


def validate_run_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != RUN_MANIFEST_VERSION:
        errors.append(f"run_manifest.schema_version must be {RUN_MANIFEST_VERSION}")
    if not manifest.get("prd_id") or not manifest.get("input_fingerprint") or not manifest.get("profile"):
        errors.append("run_manifest.prd_id/input_fingerprint/profile required")
    return errors

