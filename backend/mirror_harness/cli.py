from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evals import evaluate_qa_dataset, format_eval_summary
from .paths import HarnessPaths
from .runtime.core import prepare_runtime, show_paths, sync_upstream
from .knowledge.service import MirrorsphereKnowledgeService
from .test_design.inputs import load_prd_text
from .test_design.parser import parse_prd
from .test_design.gaps import answers_template, apply_answers
from .test_design.scope import scope_from_profile
from .test_design.scenario_builder import build_scenarios
from .test_design.case_generator import generate_cases
from .test_design.render import render_all
from .test_design.diff import diff_cases, render_diff_md
from .test_design.utils import read_json, sha256_text, stable_id, write_json
from .test_design.contracts import CASES_SCHEMA_VERSION, GAPS_SCHEMA_VERSION, RUN_MANIFEST_VERSION
from .test_design.scope_overrides import default_scope_overrides_template, resolve_scope
from .test_design.validator import validate_cases, validate_gaps, validate_run_manifest


def yaml_dump(obj: object) -> str:
    try:
        import yaml

        return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)
    except Exception:
        # Fallback: readable JSON-like text
        return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MirrorHarness runtime utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("paths", help="Show resolved Harness paths")
    sub.add_parser("sync-upstream", help="Sync config assets into upstream DeerFlow")
    sub.add_parser("prepare-runtime", help="Prepare runtime directories and sync upstream assets")
    sub.add_parser("build-index", help="Build Mirrorsphere knowledge index")
    sub.add_parser("export-kb", help="Export Mirrorsphere knowledge pack")
    eval_parser = sub.add_parser("eval-qa", help="Evaluate Mirrorsphere knowledge Q&A dataset")
    eval_parser.add_argument("--dataset", help="Path to evaluation dataset JSON file")
    eval_parser.add_argument("--report", help="Path to save evaluation report JSON")
    eval_parser.add_argument("--summary", help="Path to save CI-friendly evaluation summary JSON")
    eval_parser.add_argument("--top-k", type=int, default=8, help="Number of evidence chunks to retrieve")
    eval_parser.add_argument("--min-pass-rate", type=float, default=0.8, help="Minimum pass rate required for CI success")
    eval_parser.add_argument("--fail-on-threshold", action="store_true", help="Exit with non-zero status if pass rate is below min-pass-rate")
    ask_parser = sub.add_parser("ask", help="Ask a Mirrorsphere platform question")
    ask_parser.add_argument("query", help="Question to ask")
    ask_parser.add_argument("--top-k", type=int, default=8, help="Number of evidence chunks to retrieve")

    prd_parse = sub.add_parser("prd-parse", help="Parse PRD into normalized model and gaps")
    prd_parse.add_argument("--in", dest="inputs", nargs="+", required=True, help="PRD input files (md/txt/docx/pdf supported)")
    prd_parse.add_argument("--out", required=True, help="Output directory for artifacts")
    prd_parse.add_argument("--prd-id", help="Optional PRD id")

    prd_cases = sub.add_parser("prd-to-cases", help="Generate test cases from PRD with confirmation loop")
    prd_cases.add_argument("--in", dest="inputs", nargs="+", required=True, help="PRD input files (md/txt/docx/pdf supported)")
    prd_cases.add_argument("--out", required=True, help="Output directory for artifacts")
    prd_cases.add_argument("--answers", help="Path to answers.json (for gaps)")
    prd_cases.add_argument("--profile", default="standard", choices=["minimal", "standard", "strict"], help="Coverage profile")
    prd_cases.add_argument("--prd-id", help="Optional PRD id")
    prd_cases.add_argument("--scope-overrides", help="Path to scope_overrides.yaml (optional)")
    prd_cases.add_argument("--strict", action="store_true", help="Fail if artifact validation fails")

    prd_diff = sub.add_parser("prd-diff", help="Diff latest cases.json against previous baseline")
    prd_diff.add_argument("--old", help="Old cases.json path")
    prd_diff.add_argument("--new", required=True, help="New cases.json path")
    prd_diff.add_argument("--out", help="Output diff.md path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = HarnessPaths.detect()
    service = MirrorsphereKnowledgeService(paths)

    if args.command == "paths":
        print(json.dumps(show_paths(paths), ensure_ascii=False, indent=2))
        return 0
    if args.command == "sync-upstream":
        print(json.dumps(sync_upstream(paths), ensure_ascii=False, indent=2))
        return 0
    if args.command == "prepare-runtime":
        print(json.dumps(prepare_runtime(paths), ensure_ascii=False, indent=2))
        return 0
    if args.command == "build-index":
        print(service.build_index())
        return 0
    if args.command == "export-kb":
        print(service.export_pack())
        return 0
    if args.command == "eval-qa":
        summary = evaluate_qa_dataset(
            paths,
            dataset_path=Path(args.dataset) if args.dataset else None,
            report_path=Path(args.report) if args.report else None,
            summary_path=Path(args.summary) if args.summary else None,
            top_k=args.top_k,
            min_pass_rate=args.min_pass_rate,
        )
        print(format_eval_summary(summary))
        if args.fail_on_threshold and summary["pass_rate"] < args.min_pass_rate:
            return 2
        return 0
    if args.command == "ask":
        print(service.ask(args.query, top_k=args.top_k).answer)
        return 0
    if args.command == "prd-parse":
        out_dir = Path(args.out)
        inputs = [Path(p) for p in args.inputs]
        prd = load_prd_text(inputs)
        model = parse_prd(prd, prd_id=args.prd_id)
        write_json(out_dir / "normalized_prd.json", prd.to_dict())
        write_json(out_dir / "requirement_model.json", model.to_dict())
        write_json(out_dir / "gaps.json", {"schema_version": GAPS_SCHEMA_VERSION, "gaps": [g.to_dict() for g in model.gaps]})
        write_json(out_dir / "answers.template.json", answers_template(model))
        # Provide a default scope_overrides.yaml template for iterative refinement
        scope_tpl_path = out_dir / "scope_overrides.yaml"
        if not scope_tpl_path.exists():
            scope_tpl_path.write_text(
                "# Controls which PRD sections generate test cases and how dense the generation is.\n"
                + yaml_dump(default_scope_overrides_template()),
                encoding="utf-8",
            )
        rendered = render_all(model, out_dir)
        print(json.dumps({k: str(v) for k, v in rendered.items()}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "prd-to-cases":
        out_dir = Path(args.out)
        inputs = [Path(p) for p in args.inputs]
        prd = load_prd_text(inputs)
        prd_text_fp = sha256_text(prd.text)
        prd_id = args.prd_id or stable_id("PRD", prd.title, length=8)

        baseline_path = out_dir / "cases.json"
        old_cases = read_json(baseline_path) if baseline_path.exists() else None

        model = parse_prd(prd, prd_id=prd_id)
        if args.answers:
            ans = read_json(Path(args.answers))
            if isinstance(ans, dict):
                model = apply_answers(model, ans)
        scope_overrides_path = Path(args.scope_overrides) if args.scope_overrides else (out_dir / "scope_overrides.yaml")
        scope, include_categories, exclude_categories = resolve_scope(args.profile, scope_overrides_path)
        model = build_scenarios(model, scope, include_categories=include_categories, exclude_categories=exclude_categories)
        model = generate_cases(model, scope)

        cases = model.to_dict()
        cases["schema_version"] = CASES_SCHEMA_VERSION
        write_json(out_dir / "normalized_prd.json", prd.to_dict())
        write_json(out_dir / "cases.json", cases)
        write_json(out_dir / "gaps.json", {"schema_version": GAPS_SCHEMA_VERSION, "gaps": [g.to_dict() for g in model.gaps]})
        write_json(out_dir / "answers.template.json", answers_template(model))
        write_json(
            out_dir / "run_manifest.json",
            {
                "schema_version": RUN_MANIFEST_VERSION,
                "prd_id": prd_id,
                "input_fingerprint": prd_text_fp,
                "profile": args.profile,
                "scope_overrides": str(scope_overrides_path) if scope_overrides_path and scope_overrides_path.exists() else "",
            },
        )

        rendered = render_all(model, out_dir)

        diff = diff_cases(old_cases, cases)
        diff_md = render_diff_md(diff)
        (out_dir / "diff.md").write_text(diff_md, encoding="utf-8")
        write_json(out_dir / "diff.json", diff)

        # Validate artifacts (strict mode fails the command)
        v_errors: list[str] = []
        v_errors.extend(validate_cases(cases))
        v_errors.extend(validate_gaps(read_json(out_dir / "gaps.json")))
        v_errors.extend(validate_run_manifest(read_json(out_dir / "run_manifest.json")))
        if v_errors and args.strict:
            print("Artifact validation failed:\n" + "\n".join(f"- {e}" for e in v_errors))
            return 2

        print(json.dumps({**{k: str(v) for k, v in rendered.items()}, "cases": str(out_dir / "cases.json"), "diff": str(out_dir / "diff.md")}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "prd-diff":
        old = read_json(Path(args.old)) if args.old else None
        new = read_json(Path(args.new))
        d = diff_cases(old, new)
        md = render_diff_md(d)
        if args.out:
            Path(args.out).write_text(md, encoding="utf-8")
        else:
            print(md)
        return 0
    return 1
