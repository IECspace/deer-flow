from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportRef:
    file: str
    line: int
    module: str


def _iter_python_files(package_root: Path) -> list[Path]:
    return sorted(p for p in package_root.rglob("*.py") if "__pycache__" not in p.parts)


def _parse_imports(py_file: Path) -> list[ImportRef]:
    refs: list[ImportRef] = []
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                refs.append(ImportRef(file=str(py_file), line=node.lineno, module=alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            # Convert relative imports to a dotted-ish hint for rule checks.
            if node.level and node.level > 0:
                prefix = "." * node.level
                refs.append(ImportRef(file=str(py_file), line=node.lineno, module=f"{prefix}{node.module}"))
            else:
                refs.append(ImportRef(file=str(py_file), line=node.lineno, module=node.module))
    return refs


def check_dependency_directions(package_root: Path) -> list[str]:
    """Enforce domain dependency rules to keep layering clean."""
    violations: list[str] = []

    def rel(p: Path) -> str:
        return p.relative_to(package_root).as_posix()

    def file_domain(rel_path: str) -> str:
        top = rel_path.split("/", 1)[0]
        if top in {"knowledge", "test_design", "runtime", "evals", "mcp", "assets"}:
            return top
        return "top"

    # Domain dependency policy (strict):
    # - runtime must not be imported by other domains (it is orchestration + sync layer)
    # - requirement must not import runtime
    # - knowledge must not import runtime or requirement
    forbidden: dict[str, set[str]] = {
        "knowledge": {"runtime", "test_design"},
        "test_design": {"runtime"},
        "evals": {"runtime", "test_design"},  # evals should evaluate knowledge / contracts, not call generators
        # top-level entrypoints are allowed to orchestrate runtime
    }

    for py in _iter_python_files(package_root):
        r = rel(py)
        dom = file_domain(r)
        for ref in _parse_imports(py):
            mod = ref.module
            # Normalize to domain name for both absolute and relative.
            for target_dom in ("knowledge", "test_design", "runtime", "evals"):
                if mod.startswith(f"mirror_harness.{target_dom}") or mod.startswith(target_dom) or mod.startswith(f".{target_dom}"):
                    if target_dom in forbidden.get(dom, set()):
                        violations.append(f"{rel(Path(ref.file))}:{ref.line} forbidden import: {mod} (domain={dom} -> {target_dom})")
                    break

    return violations


def main() -> int:
    package_root = Path(__file__).resolve().parent
    violations = check_dependency_directions(package_root)
    if violations:
        print("MirrorHarness dependency-direction check failed:")
        for v in violations:
            print(f"- {v}")
        return 2
    print("MirrorHarness dependency-direction check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

