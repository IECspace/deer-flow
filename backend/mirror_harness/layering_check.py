from __future__ import annotations

from pathlib import Path


ALLOWED_TOP_LEVEL = {
    "__init__.py",
    "__main__.py",
    "cli.py",
    "deps_check.py",
    "layering_check.py",
    "paths.py",
}

# Allowed domain directories
ALLOWED_DIRS = {
    "assets",
    "knowledge",
    "test_design",
    "runtime",
    "evals",
    "mcp",
}


def check_strict_layering(package_root: Path) -> list[str]:
    """Return a list of human-readable violations."""
    violations: list[str] = []
    for p in sorted(package_root.iterdir()):
        if p.is_dir():
            if p.name in ALLOWED_DIRS or p.name == "__pycache__":
                continue
            violations.append(f"unexpected top-level directory: {p.name}")
            continue
        if p.is_file():
            if p.name in ALLOWED_TOP_LEVEL:
                continue
            violations.append(f"unexpected top-level file: {p.name}")
    return violations


def main() -> int:
    package_root = Path(__file__).resolve().parent
    violations = check_strict_layering(package_root)
    if violations:
        print("MirrorHarness layering check failed:")
        for v in violations:
            print(f"- {v}")
        return 2
    print("MirrorHarness layering check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

