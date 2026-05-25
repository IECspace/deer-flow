from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..paths import HarnessPaths
from .indexer import build_index, compute_source_hash, load_index, save_index
from .kb_exporter import export_knowledge_pack
from .models import AnswerResult, RetrievalHit
from .retriever import retrieve, tokenize

FRONTEND_API_REFERENCES = {
    "record": "pilot_web/src/apis/recording.ts",
    "recording": "pilot_web/src/apis/recording.ts",
    "replay": "pilot_web/src/apis/replay.ts",
    "mock": "pilot_web/src/apis/mock.ts",
    "diff": "pilot_web/src/apis/diff.ts",
}
FRONTEND_PAGE_REFERENCES = {
    "record": "pilot_web/src/pages/recording",
    "recording": "pilot_web/src/pages/recording",
    "replay": "pilot_web/src/pages/replay",
    "mock": "pilot_web/src/pages/mock",
    "worker": "pilot_web/src/pages/worker",
    "agent": "pilot_web/src/pages/agent",
}
APPROVAL_REFERENCES = {
    "record": "portal/biz/service/hybrid_service/approve_record.go",
    "replay": "portal/biz/service/hybrid_service/approve_replay.go",
    "mock": "portal/biz/service/hybrid_service/approve_mock.go",
}


class MirrorsphereKnowledgeService:
    def __init__(self, paths: HarnessPaths) -> None:
        self.paths = paths

    def _ensure_current_index(self) -> Path:
        current_hash = compute_source_hash(self.paths.mirrorsphere_root)
        if not self.paths.knowledge_index_path.exists():
            return self.build_index()
        index = load_index(self.paths.knowledge_index_path)
        if index.source_hash != current_hash:
            return self.build_index()
        return self.paths.knowledge_index_path

    def build_index(self) -> Path:
        index = build_index(self.paths.mirrorsphere_root)
        save_index(index, self.paths.knowledge_index_path)
        return self.paths.knowledge_index_path

    def export_pack(self) -> Path:
        self._ensure_current_index()
        index = load_index(self.paths.knowledge_index_path)
        return export_knowledge_pack(index, self.paths.knowledge_pack_path)

    def ask(self, query: str, top_k: int = 8) -> AnswerResult:
        self._ensure_current_index()
        index = load_index(self.paths.knowledge_index_path)
        hits = retrieve(index, query, top_k=top_k)
        return AnswerResult(query=query, answer=self._draft_answer(query, hits), evidence=hits)

    def _draft_answer(self, query: str, hits: list[RetrievalHit]) -> str:
        if not hits:
            return (
                "当前内部知识库没有检索到直接证据。Mirrorsphere 相关问题只允许基于内部知识库和仓库文件作答，"
                "因此这里不会补充外部世界知识。建议把问题收窄到具体模块，例如 record、replay、mock、diff、"
                "portal、pilot_web、agent、worker、airtest。"
            )

        tag_counter = Counter(tag for hit in hits for tag in hit.chunk.tags)
        dominant_tags = [tag for tag, _ in tag_counter.most_common(4)]
        query_terms = set(tokenize(query))
        paths = [hit.chunk.path for hit in hits[:6]]
        matched_terms = sorted({term for hit in hits for term in hit.matched_terms})
        low_confidence = self._is_low_confidence(query_terms, matched_terms, hits)
        if self._should_caution_support_query(query, query_terms, matched_terms, hits):
            low_confidence = True
        overview_query = self._is_overview_query(query, query_terms)

        lines: list[str] = []
        lines.append("Mirrorsphere 知识问答结果")
        lines.append("")
        lines.append(f"问题：{query}")
        lines.append("")
        lines.append("回答边界：以下内容仅基于 Mirrorsphere 内部知识库、仓库文件和已索引文档；未被内部证据支持的内容不会补充外部世界知识。")
        lines.append("")
        if dominant_tags:
            lines.append(f"高相关领域：{', '.join(dominant_tags)}")
            lines.append("")
        lines.append("初步结论：")
        for idx, item in enumerate(
            self._build_summary_lines(query, query_terms, paths, dominant_tags, low_confidence, overview_query),
            start=1,
        ):
            lines.append(f"{idx}. {item}")
        lines.append("")
        lines.append("关键证据：")
        for hit in hits[:5]:
            rel = hit.chunk.path
            span = f"L{hit.chunk.start_line}-L{hit.chunk.end_line}"
            preview = self._compact_text(hit.chunk.text)
            lines.append(f"- {rel} ({span})")
            lines.append(f"  {preview}")
        lines.append("")
        lines.append("建议下一步：")
        for step in self._build_next_steps(query_terms, dominant_tags, hits, low_confidence, overview_query):
            lines.append(f"- {step}")
        return "\n".join(lines)

    def _is_overview_query(self, query: str, query_terms: set[str]) -> bool:
        query_lower = query.lower()
        return (
            any(flag in query for flag in ("是什么", "简介", "介绍", "做什么"))
            or any(term in query_terms for term in {"overview", "definition", "intro"})
            or query_lower.strip() in {"mirrorsphere", "mirrorsphere是什么"}
        )

    def _should_caution_support_query(
        self,
        query: str,
        query_terms: set[str],
        matched_terms: list[str],
        hits: list[RetrievalHit],
    ) -> bool:
        query_lower = query.lower()
        if not any(flag in query_lower for flag in ("支持", "内置", "有没有", "有吗", "是否有")):
            return False
        ignored = {
            "mirrorsphere",
            "支持",
            "内置",
            "有没有",
            "有吗",
            "是否有",
            "模块",
            "能力",
            "功能",
            "吗",
        }
        meaningful_terms = {term for term in query_terms if term not in ignored}
        unmatched = meaningful_terms - set(matched_terms)
        top_score = hits[0].score if hits else 0.0
        return bool(unmatched) or top_score < 12.0

    def _build_summary_lines(
        self,
        query: str,
        query_terms: set[str],
        paths: list[str],
        dominant_tags: list[str],
        low_confidence: bool,
        overview_query: bool,
    ) -> list[str]:
        lines: list[str] = []
        query_lower = query.lower()
        if overview_query:
            lines.append("根据当前仓库中的平台定义文档，Mirrorsphere 是一个面向流量录制、流量回放、Mock、Diff、API 测试和 UI 自动化的测试与验证平台。")
            lines.append("它不是单一的录制器或回放器，而是由 portal、pilot_web、recorder、replayer、airtest-agent 等模块共同组成的平台。")
            lines.append("在 AI 体系中，harness 是 Mirrorsphere 的 AI 扩展层，基于 DeerFlow 提供知识问答与后续智能能力。")
            lines.append("平台定义的首选依据可先看：harness/docs/overview.md")
        if low_confidence:
            if any(flag in query_lower for flag in ("支持", "内置", "有没有", "有吗", "是否有")):
                lines.append("当前知识库里没有检索到能直接证明该能力已经内置或正式支持的强证据，不建议直接下结论为“支持”。")
            else:
                lines.append("当前没有检索到能直接坐实该问题的强证据，下面只给出内部知识库中最接近的入口和仍需确认的部分。")
        if {"接入", "开始", "模块"} & query_terms:
            lines.append("如果是初次接入 Mirrorsphere，建议先按 portal -> pilot_web -> recorder/replayer -> airtest-agent 的顺序建立整体认知。")
        if {"ui", "自动化", "airtest"} & query_terms:
            lines.append("Mirrorsphere 具备 UI 自动化能力，核心执行节点是 airtest-agent，平台侧还有 ui_airtest 相关服务。")
        if {"approve", "approval", "审批"} & query_terms:
            lines.append("审批相关逻辑更可能集中在 portal 服务层，而不是前端页面本身。")
        if {"page", "页面", "前端"} & query_terms:
            lines.append("页面入口优先看 pilot_web/src/pages，下游接口定义优先看 pilot_web/src/apis。")
        if {"api", "接口"} & query_terms:
            lines.append("接口能力通常在 portal/biz/handler 和 portal/biz/service 双层体现。")
        if {"record", "replay", "mock", "diff"} & query_terms:
            lines.append("这几个能力在 Mirrorsphere 中是串联关系，不是孤立模块。")
        lines.extend(self._build_targeted_guidance(query_terms))
        if not lines:
            lines.append("从当前证据看，问题涉及的知识点主要分布在以下文件中。")
        for path in paths[:3]:
            lines.append(f"高优先级入口文件：{path}")
        if dominant_tags:
            lines.append(f"从标签分布看，这次问题最接近 {', '.join(dominant_tags)} 相关能力。")
        return lines

    def _build_next_steps(
        self,
        query_terms: set[str],
        dominant_tags: list[str],
        hits: list[RetrievalHit],
        low_confidence: bool,
        overview_query: bool,
    ) -> list[str]:
        steps: list[str] = []
        if overview_query:
            steps.append("如果是平台介绍类问题，优先以 harness/docs/overview.md 和 harness/README.md 为准。")
        if low_confidence:
            steps.append("把问题收窄到具体页面、接口、service 或执行器名称，下一轮问答会更稳定。")
        if "pilot-web" in dominant_tags:
            steps.append("先从 pilot_web 页面和 apis 对齐前端入口与接口调用。")
        if "portal" in dominant_tags or any("portal/" in hit.chunk.path for hit in hits):
            steps.append("再沿着 portal handler -> service -> dal 继续定位真实业务逻辑。")
        if "record" in dominant_tags:
            steps.append("录制相关问题优先对照 recorder 与 portal/biz/service/record_service。")
        if "replay" in dominant_tags:
            steps.append("回放相关问题优先对照 replayer 与 portal/biz/service/replay_service。")
        if "mock" in dominant_tags:
            steps.append("Mock 问题优先查看 portal/biz/service/mock_service 与 pilot_web/src/pages/mock。")
        if "diff" in dominant_tags:
            steps.append("Diff 问题优先查看 pilot_web/src/apis/diff.ts 与 portal/biz/handler/diffy。")
        if {"支持", "内置", "有没有", "有吗"} & query_terms:
            steps.append("如果是想确认是否已正式支持某项能力，建议再补一个更具体的模块名或对照产品文档。")
        if not steps:
            steps.append("把问题收窄到具体模块或文件名，能得到更稳定的证据。")
        return steps

    def _build_targeted_guidance(self, query_terms: set[str]) -> list[str]:
        lines: list[str] = []
        if {"page", "页面", "前端", "api", "接口"} & query_terms:
            for workflow_term, path in FRONTEND_API_REFERENCES.items():
                if workflow_term in query_terms:
                    lines.append(f"更具体的前端接口定义可先看：{path}")
                    break
        if {"page", "页面", "前端"} & query_terms:
            for workflow_term, path in FRONTEND_PAGE_REFERENCES.items():
                if workflow_term in query_terms:
                    lines.append(f"对应页面入口通常从这里开始：{path}")
                    break
        if {"approve", "approval", "审批"} & query_terms:
            for workflow_term, path in APPROVAL_REFERENCES.items():
                if workflow_term in query_terms:
                    lines.append(f"审批后端主入口可先看：{path}")
                    break
        return lines

    def _compact_text(self, text: str, limit: int = 220) -> str:
        one_line = " ".join(part.strip() for part in text.splitlines() if part.strip())
        if len(one_line) <= limit:
            return one_line
        return f"{one_line[:limit].rstrip()}..."

    def _is_low_confidence(self, query_terms: set[str], matched_terms: list[str], hits: list[RetrievalHit]) -> bool:
        if not hits:
            return True
        ignored = {"mirrorsphere", "支持", "模块", "开始", "能力", "功能", "几个", "先看", "在哪", "吗", "有吗", "有没有"}
        meaningful_terms = [term for term in query_terms if term not in ignored]
        if not meaningful_terms:
            return False
        matched = {term for term in matched_terms if term not in ignored}
        coverage = len(matched & set(meaningful_terms)) / len(set(meaningful_terms))
        unmatched = [term for term in meaningful_terms if term not in matched]
        top_score = hits[0].score
        return coverage < 0.45 or top_score < 8.0 or len(unmatched) >= 2

