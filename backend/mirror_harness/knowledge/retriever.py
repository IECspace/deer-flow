from __future__ import annotations

import math
import re
from collections import Counter

from .models import KnowledgeIndex, RetrievalHit


TOKEN_RE = re.compile(r"[A-Za-z0-9_\-./]+|[\u4e00-\u9fff]{1,8}")
STOP_TERMS = {
    "the",
    "is",
    "a",
    "an",
    "to",
    "of",
    "and",
    "or",
    "in",
    "on",
    "for",
    "what",
    "how",
    "where",
    "哪个",
    "怎么",
    "什么",
    "一下",
    "相关",
}
ALIASES = {
    "是什么": ("overview", "definition", "intro", "docs", "readme"),
    "简介": ("overview", "intro", "docs", "readme"),
    "介绍": ("overview", "intro", "docs", "readme"),
    "做什么": ("overview", "definition", "capability"),
    "回放": ("replay",),
    "录制": ("record", "recording", "recorder"),
    "mock": ("mock",),
    "差异": ("diff", "diffy"),
    "对比": ("diff", "diffy"),
    "审批": ("approve", "approval"),
    "页面": ("page", "pilot_web"),
    "前端": ("page", "pilot_web"),
    "前端代码": ("pilot_web", "pages", "apis"),
    "前后端": ("pilot_web", "portal"),
    "接口": ("api",),
    "调用接口": ("api", "apis"),
    "服务": ("service",),
    "业务": ("biz",),
    "环境": ("env",),
    "注册": ("register",),
    "调度": ("schedule",),
    "执行": ("execute", "handler", "runner"),
    "执行器": ("handler", "runner", "worker"),
    "入口": ("handler", "main"),
    "架构": ("architecture", "harness", "docs"),
    "文档": ("docs", "readme", "roadmap"),
    "扩展": ("harness", "ai"),
    "路线图": ("roadmap",),
    "接入": ("readme", "architecture", "docs", "portal", "pilot_web", "recorder", "replayer", "airtest-agent"),
    "开始": ("readme", "architecture", "docs"),
    "模块": ("portal", "pilot_web", "recorder", "replayer", "airtest-agent"),
    "能力": ("readme", "architecture", "docs"),
    "自动化": ("airtest", "ui_airtest", "airtest-agent"),
    "失败": ("report", "diff", "replayer", "handler"),
    "报错": ("failure", "report", "handler", "service"),
    "日志": ("log", "report"),
    "链路": ("workflow", "handler", "service"),
    "录制器": ("record", "agent"),
    "回放器": ("replay", "worker"),
}
WORKFLOW_TERMS = {"record", "replay", "mock", "diff"}
FRONTEND_API_PATHS = {
    "record": "pilot_web/src/apis/recording.ts",
    "recording": "pilot_web/src/apis/recording.ts",
    "replay": "pilot_web/src/apis/replay.ts",
    "mock": "pilot_web/src/apis/mock.ts",
    "diff": "pilot_web/src/apis/diff.ts",
}
FRONTEND_PAGE_HINTS = {
    "record": "pilot_web/src/pages/recording/",
    "recording": "pilot_web/src/pages/recording/",
    "replay": "pilot_web/src/pages/replay/",
    "mock": "pilot_web/src/pages/mock/",
    "diff": "pilot_web/src/pages/diff/",
    "worker": "pilot_web/src/pages/worker/",
    "agent": "pilot_web/src/pages/agent/",
}
APPROVAL_PATHS = {
    "record": "portal/biz/service/hybrid_service/approve_record.go",
    "replay": "portal/biz/service/hybrid_service/approve_replay.go",
    "mock": "portal/biz/service/hybrid_service/approve_mock.go",
}


def tokenize(text: str) -> list[str]:
    terms = [term.lower() for term in TOKEN_RE.findall(text)]
    tokens = [term for term in terms if term not in STOP_TERMS and len(term.strip()) > 1]
    expanded = list(tokens)
    for phrase, alias_terms in ALIASES.items():
        if phrase in text:
            expanded.extend(alias_terms)
    return sorted(set(expanded))


def _score(query_terms: list[str], path: str, text: str, tags: list[str]) -> tuple[float, list[str]]:
    if not query_terms:
        return 0.0, []
    haystack_terms = tokenize(f"{path} {' '.join(tags)} {text}")
    counter = Counter(haystack_terms)
    matched_terms: list[str] = []
    score = 0.0
    for term in query_terms:
        freq = counter.get(term, 0)
        if freq:
            matched_terms.append(term)
            score += 2.0 + math.log(freq + 1.0)
        if term in path.lower():
            score += 4.0
        if term in tags:
            score += 3.5
    lowered_path = path.lower()
    top_level = lowered_path.split("/", 1)[0]
    workflow_overlap = len(set(query_terms) & WORKFLOW_TERMS)
    query_term_set = set(query_terms)
    if top_level in {"portal", "pilot_web", "recorder", "replayer", "airtest-agent"}:
        score += 1.5
    if {"readme", "docs", "architecture", "overview", "intro", "definition"} & query_term_set:
        if lowered_path.endswith("readme.md") or "/docs/" in lowered_path:
            score += 2.0
    if {"overview", "intro", "definition"} & query_term_set:
        if lowered_path == "harness/docs/overview.md":
            score += 10.0
        if lowered_path == "harness/readme.md":
            score += 5.0
    if workflow_overlap >= 3 and any(term in lowered_path for term in ("record", "replay", "mock", "diff", "architecture.md", "readme.md")):
        score += 2.0
    if "/biz/service/" in lowered_path:
        score += 2.5
    if "/biz/handler/" in lowered_path:
        score += 2.0
    if "/src/apis/" in lowered_path or "/src/pages/" in lowered_path:
        score += 2.0
    if "api" in query_terms and lowered_path.startswith("pilot_web/src/apis/"):
        score += 3.5
    if "page" in query_terms and lowered_path.startswith("pilot_web/src/pages/"):
        score += 2.5
    if {"portal", "service"} & query_term_set and "/biz/service/" in lowered_path:
        score += 1.5

    for workflow_term, api_path in FRONTEND_API_PATHS.items():
        if workflow_term in query_terms and lowered_path == api_path:
            score += 7.0
            if "api" in query_terms:
                score += 3.0

    for workflow_term, page_hint in FRONTEND_PAGE_HINTS.items():
        if workflow_term in query_terms and lowered_path.startswith(page_hint):
            score += 4.0
            if "page" in query_terms:
                score += 2.0

    for workflow_term, approval_path in APPROVAL_PATHS.items():
        if workflow_term in query_terms and lowered_path == approval_path:
            score += 5.0
            if "approval" in query_terms or "approve" in query_terms:
                score += 2.0

    if "/pages/api-test/" in lowered_path and "api-test" not in query_terms:
        score -= 3.0
    if "/layouts/" in lowered_path or lowered_path.endswith("/index.ts"):
        score -= 2.0
    if lowered_path.endswith("readme.md") or "/docs/" in lowered_path:
        score += 0.5
    if lowered_path.startswith("harness/docs/"):
        score -= 1.0
    if "orm_gen" in lowered_path or "model/query" in lowered_path or ".pb.go" in lowered_path:
        score -= 4.0
    return score, matched_terms


def retrieve(index: KnowledgeIndex, query: str, top_k: int = 8) -> list[RetrievalHit]:
    query_terms = tokenize(query)
    hits: list[RetrievalHit] = []
    for chunk in index.chunks:
        score, matched_terms = _score(query_terms, chunk.path, chunk.text, chunk.tags)
        if score <= 0:
            continue
        hits.append(RetrievalHit(chunk=chunk, score=score, matched_terms=sorted(set(matched_terms))))
    hits.sort(key=lambda item: item.score, reverse=True)
    selected: list[RetrievalHit] = []
    seen_paths: set[str] = set()
    module_counts: Counter[str] = Counter()
    for hit in hits:
        path = hit.chunk.path
        module = path.split("/", 1)[0]
        if path in seen_paths:
            continue
        if module_counts[module] >= 3:
            continue
        selected.append(hit)
        seen_paths.add(path)
        module_counts[module] += 1
        if len(selected) >= top_k:
            break
    return selected

