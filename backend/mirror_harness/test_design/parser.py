from __future__ import annotations

import re

from .models import DesignItem, DesignModule, GapQuestion, NormalizedPRD, SourceRef, TestDesignModel
from .utils import stable_id


def parse_prd(prd: NormalizedPRD, prd_id: str | None = None) -> TestDesignModel:
    prd_id = prd_id or stable_id("PRD", prd.title, length=8)
    modules = _extract_modules_and_requirements(prd)
    gaps = detect_gaps(prd, modules)
    return TestDesignModel(prd_id=prd_id, title=prd.title, source=_source_hint(prd), modules=modules, gaps=gaps)


def _source_hint(prd: NormalizedPRD) -> str:
    if prd.sources:
        return prd.sources[0].source
    return ""


def _extract_modules_and_requirements(prd: NormalizedPRD) -> list[DesignModule]:
    lines = prd.text.splitlines()

    current_module = DesignModule(module_id="M1", name="General", category="functional")
    modules: list[DesignModule] = [current_module]
    req_idx = 0

    for i, raw in enumerate(lines, start=1):
        s = raw.rstrip().strip()
        if not s:
            continue
        if s.startswith("# "):
            name = s[2:].strip()[:120] or "General"
            current_module = DesignModule(module_id=stable_id("M", name, length=6), name=name, category=_infer_category(name))
            modules.append(current_module)
            continue
        if s.startswith("## "):
            name = s[3:].strip()[:120]
            current_module = DesignModule(module_id=stable_id("M", name, length=6), name=name, category=_infer_category(name))
            modules.append(current_module)
            continue

        stmt = _parse_requirement_statement(s)
        if not stmt:
            continue
        if current_module.category in {"rollout", "risk", "analytics"}:
            continue

        req_idx += 1
        rid = f"R{req_idx}"
        trace = [SourceRef(source=_source_hint(prd), locator=f"L{i}")]
        current_module.requirements.append(DesignItem(requirement_id=rid, statement=stmt, trace=trace))

    cleaned = [m for m in modules if m.requirements] or [DesignModule(module_id="M1", name="General", category="functional")]
    return cleaned


def _infer_category(title: str) -> str:
    if any(k in title for k in ("非功能", "性能", "安全", "兼容", "可用性")):
        return "nonfunctional"
    if any(k in title for k in ("埋点", "指标", "事件")):
        return "analytics"
    if any(k in title for k in ("上线", "发布", "开发阶段", "测试阶段")):
        return "rollout"
    if any(k in title for k in ("风险", "依赖")):
        return "risk"
    if any(k in title for k in ("数据", "表")):
        return "data"
    return "functional"


def _parse_requirement_statement(line: str) -> str | None:
    m = re.match(r"^[-*]\s+(.*)$", line)
    if m:
        stmt = m.group(1).strip()
        return stmt if _is_requirement_like(stmt) else None
    m = re.match(r"^\d+[\.\)]\s+(.*)$", line)
    if m:
        stmt = m.group(1).strip()
        return stmt if _is_requirement_like(stmt) else None
    for prefix in ("需求：", "需求:", "功能：", "功能:", "目标：", "目标:"):
        if line.startswith(prefix):
            stmt = line[len(prefix) :].strip()
            return stmt if stmt else None
    return None


def _is_requirement_like(text: str) -> bool:
    if len(text) < 6:
        return False
    if text.endswith("：") or text.endswith(":"):
        return False
    return True


def detect_gaps(prd: NormalizedPRD, modules: list[DesignModule]) -> list[GapQuestion]:
    text = prd.text
    gaps: list[GapQuestion] = []

    def add(qid: str, q: str, why: str) -> None:
        gaps.append(GapQuestion(question_id=qid, question=q, why_it_matters=why))

    if not _contains_any(text, ["角色", "用户", "管理员", "权限", "RBAC"]):
        add("actors_roles", "本需求涉及哪些用户角色/权限边界？", "权限差异会直接影响用例覆盖（成功/拒绝/越权）。")
    if not _contains_any(text, ["验收", "验收标准", "AC", "Acceptance Criteria"]):
        add("acceptance_criteria", "每个核心功能的验收标准是什么（可量化/可判定）？", "没有验收标准会导致期望结果与断言点不明确。")
    if not _contains_any(text, ["范围", "不包含", "out of scope", "不在范围"]):
        add("scope_in_out", "本 PRD 的 in-scope / out-of-scope 是什么？", "范围不清会造成用例过多或漏测关键模块。")
    if not _contains_any(text, ["数据", "字段", "参数", "示例", "mock"]):
        add("test_data", "是否有关键数据字段/示例请求/业务数据约束？", "测试数据决定可执行性，影响边界/异常覆盖。")
    if not _contains_any(text, ["兼容", "版本", "灰度", "回滚", "降级"]):
        add("release_strategy", "是否有灰度/兼容/回滚/降级策略要求？", "发布策略决定兼容性与回归用例维度。")
    if not _contains_any(text, ["性能", "QPS", "SLA", "延迟", "容量"]):
        add("nfr_perf", "是否有性能/容量指标（SLA、p95、QPS）？", "NFR 约束会带来专项用例与门槛。")
    if not any(m.requirements for m in modules):
        add("requirements_missing", "PRD 中是否能提供更明确的功能点列表（条目化）？", "需要功能点切片才能稳定生成场景与用例。")

    return gaps


def _contains_any(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(k.lower() in lower for k in keywords)

