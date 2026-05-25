from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..paths import HarnessPaths
from ..knowledge.service import MirrorsphereKnowledgeService


@dataclass(slots=True)
class QAEvalCase:
    case_id: str
    question: str
    category: str
    expected_paths: list[str]
    required_keywords: list[str]
    required_any_keywords: list[list[str]]
    optional_keywords: list[str]
    expected_tags: list[str]
    forbidden_paths: list[str]
    forbidden_keywords: list[str]
    pass_threshold: float

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "QAEvalCase":
        return cls(
            case_id=raw["id"],
            question=raw["question"],
            category=raw.get("category", "general"),
            expected_paths=list(raw.get("expected_paths", [])),
            required_keywords=list(raw.get("required_keywords", [])),
            required_any_keywords=[list(group) for group in raw.get("required_any_keywords", [])],
            optional_keywords=list(raw.get("optional_keywords", [])),
            expected_tags=list(raw.get("expected_tags", [])),
            forbidden_paths=list(raw.get("forbidden_paths", [])),
            forbidden_keywords=list(raw.get("forbidden_keywords", [])),
            pass_threshold=float(raw.get("pass_threshold", 0.6)),
        )


def load_qa_dataset(path: Path) -> list[QAEvalCase]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [QAEvalCase.from_dict(item) for item in raw]


def _normalize(text: str) -> str:
    return text.lower()


def _path_match_score(expected_paths: list[str], evidence_paths: list[str], answer_text: str) -> tuple[float, list[str]]:
    if not expected_paths:
        return 1.0, []
    answer_lower = _normalize(answer_text)
    matched: list[str] = []
    for expected in expected_paths:
        if any(path.startswith(expected) or expected.startswith(path) for path in evidence_paths):
            matched.append(expected)
            continue
        if expected.lower() in answer_lower:
            matched.append(expected)
    score = len(set(matched)) / len(expected_paths)
    return score, sorted(set(matched))


def _keyword_score(
    required_keywords: list[str],
    required_any_keywords: list[list[str]],
    optional_keywords: list[str],
    answer_text: str,
) -> tuple[float, list[str], list[str], list[str]]:
    haystack = _normalize(answer_text)
    required_hits = [keyword for keyword in required_keywords if _normalize(keyword) in haystack]
    required_any_hits = [
        " | ".join(group) for group in required_any_keywords if any(_normalize(keyword) in haystack for keyword in group)
    ]
    optional_hits = [keyword for keyword in optional_keywords if _normalize(keyword) in haystack]
    required_slot_count = len(required_keywords) + len(required_any_keywords)
    if required_slot_count:
        base = (len(required_hits) + len(required_any_hits)) / required_slot_count
    else:
        base = 1.0
    if optional_keywords:
        bonus = 0.2 * (len(optional_hits) / len(optional_keywords))
    else:
        bonus = 0.0
    return min(1.0, base + bonus), required_hits, optional_hits, required_any_hits


def _tag_score(expected_tags: list[str], evidence_tags: list[str]) -> tuple[float, list[str]]:
    if not expected_tags:
        return 1.0, []
    hits = [tag for tag in expected_tags if tag in evidence_tags]
    return len(hits) / len(expected_tags), hits


def _build_failure_diff(
    case: QAEvalCase,
    matched_paths: list[str],
    required_hits: list[str],
    optional_hits: list[str],
    required_any_hits: list[str],
    tag_hits: list[str],
    forbidden_path_hits: list[str],
    forbidden_keyword_hits: list[str],
) -> dict[str, list[str]]:
    return {
        "missing_paths": [path for path in case.expected_paths if path not in matched_paths],
        "missing_required_keywords": [keyword for keyword in case.required_keywords if keyword not in required_hits],
        "missing_required_any_keywords": [
            " | ".join(group) for group in case.required_any_keywords if " | ".join(group) not in required_any_hits
        ],
        "missing_optional_keywords": [keyword for keyword in case.optional_keywords if keyword not in optional_hits],
        "missing_tags": [tag for tag in case.expected_tags if tag not in tag_hits],
        "unexpected_paths": forbidden_path_hits,
        "unexpected_keywords": forbidden_keyword_hits,
    }


def _build_category_stats(case_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in case_reports:
        grouped[case["category"]].append(case)

    stats: list[dict[str, Any]] = []
    for category in sorted(grouped):
        cases = grouped[category]
        passed = sum(1 for case in cases if case["pass"])
        avg_score = sum(case["overall_score"] for case in cases) / len(cases)
        stats.append(
            {
                "category": category,
                "case_count": len(cases),
                "pass_count": passed,
                "pass_rate": round(passed / len(cases), 4),
                "avg_score": round(avg_score, 4),
            }
        )
    return stats


def _build_ci_summary(summary: dict[str, Any], min_pass_rate: float) -> dict[str, Any]:
    failures = [case for case in summary["cases"] if not case["pass"]]
    return {
        "generated_at": summary["generated_at"],
        "dataset_path": summary["dataset_path"],
        "top_k": summary["top_k"],
        "case_count": summary["case_count"],
        "pass_count": summary["pass_count"],
        "pass_rate": summary["pass_rate"],
        "min_pass_rate": round(min_pass_rate, 4),
        "status": "pass" if summary["pass_rate"] >= min_pass_rate else "fail",
        "category_stats": summary["category_stats"],
        "failure_count": len(failures),
        "failures": [
            {
                "id": case["id"],
                "category": case["category"],
                "question": case["question"],
                "overall_score": case["overall_score"],
                "threshold": case["threshold"],
                "failure_diff": case["failure_diff"],
            }
            for case in failures
        ],
    }


def evaluate_qa_dataset(
    paths: HarnessPaths,
    dataset_path: Path | None = None,
    top_k: int = 8,
    report_path: Path | None = None,
    summary_path: Path | None = None,
    min_pass_rate: float = 0.8,
) -> dict[str, Any]:
    dataset = load_qa_dataset(dataset_path or paths.qa_eval_dataset_path)
    service = MirrorsphereKnowledgeService(paths)

    case_reports: list[dict[str, Any]] = []
    passed = 0
    for case in dataset:
        result = service.ask(case.question, top_k=top_k)
        evidence_paths = [hit.chunk.path for hit in result.evidence]
        evidence_tags = sorted({tag for hit in result.evidence for tag in hit.chunk.tags})
        answer_lower = _normalize(result.answer)

        path_score, matched_paths = _path_match_score(case.expected_paths, evidence_paths, result.answer)
        keyword_score, required_hits, optional_hits, required_any_hits = _keyword_score(
            case.required_keywords,
            case.required_any_keywords,
            case.optional_keywords,
            result.answer,
        )
        tag_score, tag_hits = _tag_score(case.expected_tags, evidence_tags)
        forbidden_path_hits = [
            path
            for path in case.forbidden_paths
            if any(evidence.startswith(path) or path.startswith(evidence) for evidence in evidence_paths) or path.lower() in answer_lower
        ]
        forbidden_keyword_hits = [keyword for keyword in case.forbidden_keywords if _normalize(keyword) in answer_lower]
        penalty = 0.0
        if case.forbidden_paths:
            penalty += 0.25 * (len(forbidden_path_hits) / len(case.forbidden_paths))
        if case.forbidden_keywords:
            penalty += 0.25 * (len(forbidden_keyword_hits) / len(case.forbidden_keywords))

        if case.expected_paths:
            overall = (0.55 * path_score) + (0.30 * keyword_score) + (0.15 * tag_score)
        else:
            overall = (0.70 * keyword_score) + (0.30 * tag_score)
        overall = max(0.0, overall - penalty)

        is_pass = overall >= case.pass_threshold
        if is_pass:
            passed += 1
        failure_diff = _build_failure_diff(
            case,
            matched_paths,
            required_hits,
            optional_hits,
            required_any_hits,
            tag_hits,
            forbidden_path_hits,
            forbidden_keyword_hits,
        )

        case_reports.append(
            {
                "id": case.case_id,
                "question": case.question,
                "category": case.category,
                "pass": is_pass,
                "threshold": case.pass_threshold,
                "overall_score": round(overall, 4),
                "path_score": round(path_score, 4),
                "keyword_score": round(keyword_score, 4),
                "tag_score": round(tag_score, 4),
                "penalty": round(penalty, 4),
                "matched_paths": matched_paths,
                "required_hits": required_hits,
                "required_any_hits": required_any_hits,
                "optional_hits": optional_hits,
                "tag_hits": tag_hits,
                "forbidden_path_hits": forbidden_path_hits,
                "forbidden_keyword_hits": forbidden_keyword_hits,
                "evidence_paths": evidence_paths,
                "evidence_tags": evidence_tags,
                "failure_diff": failure_diff,
                "answer": result.answer,
            }
        )

    category_stats = _build_category_stats(case_reports)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset_path or paths.qa_eval_dataset_path),
        "case_count": len(dataset),
        "pass_count": passed,
        "pass_rate": round((passed / len(dataset)) if dataset else 0.0, 4),
        "top_k": top_k,
        "min_pass_rate": round(min_pass_rate, 4),
        "category_stats": category_stats,
        "cases": case_reports,
    }

    final_report_path = report_path or (paths.runtime_evaluations_dir / "knowledge-qa-report.json")
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    final_summary_path = summary_path or (paths.runtime_evaluations_dir / "knowledge-qa-summary.json")
    ci_summary = _build_ci_summary(summary, min_pass_rate=min_pass_rate)
    final_summary_path.write_text(json.dumps(ci_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def format_eval_summary(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("Mirrorsphere Knowledge Q&A Evaluation")
    lines.append("")
    lines.append(f"用例数: {summary['case_count']}")
    lines.append(f"通过数: {summary['pass_count']}")
    lines.append(f"通过率: {summary['pass_rate']:.2%}")
    lines.append(f"CI 阈值: {summary['min_pass_rate']:.2%}")
    lines.append("")
    lines.append("按分类统计:")
    for item in summary["category_stats"]:
        lines.append(f"- {item['category']}: pass={item['pass_count']}/{item['case_count']} rate={item['pass_rate']:.2%} avg={item['avg_score']:.2f}")
    lines.append("")

    failures = [case for case in summary["cases"] if not case["pass"]]
    if failures:
        lines.append("未通过用例:")
        for case in failures[:10]:
            lines.append(
                f"- {case['id']} score={case['overall_score']:.2f} "
                f"question={case['question']} "
                f"paths={', '.join(case['matched_paths']) or '-'} "
                f"keywords={', '.join(case['required_hits']) or '-'}"
            )
            diff = case["failure_diff"]
            lines.append(f"  expected-missing-paths: {', '.join(diff['missing_paths']) or '-'}")
            lines.append(f"  expected-missing-required-keywords: {', '.join(diff['missing_required_keywords']) or '-'}")
            lines.append(f"  expected-missing-required-any-keywords: {', '.join(diff['missing_required_any_keywords']) or '-'}")
            lines.append(f"  expected-missing-tags: {', '.join(diff['missing_tags']) or '-'}")
            lines.append(f"  unexpected-paths: {', '.join(diff['unexpected_paths']) or '-'}")
            lines.append(f"  unexpected-keywords: {', '.join(diff['unexpected_keywords']) or '-'}")
    else:
        lines.append("所有用例通过。")
    return "\n".join(lines)

