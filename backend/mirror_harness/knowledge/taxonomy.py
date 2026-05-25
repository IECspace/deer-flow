from __future__ import annotations

from pathlib import Path


DOMAIN_HINTS: dict[str, tuple[str, ...]] = {
    "record": ("record", "recording", "recorder"),
    "replay": ("replay", "replayer"),
    "mock": ("mock",),
    "diff": ("diff", "diffy"),
    "agent": ("agent",),
    "worker": ("worker",),
    "airtest": ("airtest", "ui_airtest", "uiairtest"),
    "api-test": ("api-test", "api_", "api/", "scene", "case"),
    "biz": ("biz", "env"),
    "portal": ("portal",),
    "pilot-web": ("pilot_web", "web", "tsx", "react"),
}

MODULE_DESCRIPTIONS: dict[str, str] = {
    "portal": "Mirrorsphere backend service and business orchestration.",
    "pilot_web": "Mirrorsphere frontend pages and API clients.",
    "recorder": "Traffic recording agent and capture flow.",
    "replayer": "Traffic replay worker and execution flow.",
    "pilot": "Shared runtime and platform support code.",
    "airtest-agent": "UI automation execution agent.",
    "harness": "Mirrorsphere AI extension layer and design docs.",
}

_SKILL_DOCS_PREFIX = "harness/src/mirror_harness/assets/custom/skills/mirrorsphere-knowledge/references/docs"
SKILL_DOCS_INDEX_PREFIX = "harness/docs"

DOC_SUFFIXES = {".md", ".txt", ".rst"}
CODE_SUFFIXES = {".go", ".py", ".ts", ".tsx", ".js", ".jsx", ".proto", ".yaml", ".yml", ".json", ".sh"}
INCLUDE_DIRS = {
    "portal",
    "pilot_web",
    "recorder",
    "replayer",
    "pilot",
    "airtest-agent",
    "harness",
}
EXCLUDE_DIRS = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    ".claude",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "output",
    "log",
    "workdir",
    "venv",
    ".venv",
    "site-packages",
}
EXCLUDE_FILE_NAMES = {
    "CLAUDE.md",
    ".env",
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "go.sum",
}
EXCLUDE_PATH_HINTS = (
    "orm_gen/",
    "model/query/",
    ".pb.go",
    "/logs/",
    "/output/",
    "/coverage/",
)


def _is_skill_docs_path(path: Path) -> bool:
    return path.as_posix().startswith(_SKILL_DOCS_PREFIX)


def normalize_index_path(path_str: str) -> str:
    if path_str.startswith(_SKILL_DOCS_PREFIX):
        return SKILL_DOCS_INDEX_PREFIX + path_str[len(_SKILL_DOCS_PREFIX):]
    return path_str


def infer_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in DOC_SUFFIXES:
        return "doc"
    if suffix in CODE_SUFFIXES:
        return "code"
    return "other"


def infer_tags(path: Path, text: str) -> list[str]:
    haystack = f"{path.as_posix()} {text.lower()}"
    tags: list[str] = []
    for tag, hints in DOMAIN_HINTS.items():
        if any(hint in haystack for hint in hints):
            tags.append(tag)
    return sorted(set(tags))


def should_index(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_DIRS:
        return False
    normalized = path.as_posix()
    if path.name in EXCLUDE_FILE_NAMES:
        return False
    if any(hint in normalized for hint in EXCLUDE_PATH_HINTS):
        return False
    top = path.parts[0] if path.parts else ""
    if top == "harness":
        if _is_skill_docs_path(path) and infer_kind(path) == "doc":
            return True
        if len(path.parts) == 2 and path.name == "README.md":
            return True
        return False
    if top not in INCLUDE_DIRS and not (len(path.parts) == 1 and path.name == "README.md"):
        return False
    return infer_kind(path) != "other"


def describe_module(name: str) -> str:
    return MODULE_DESCRIPTIONS.get(name, "Mirrorsphere repository module.")

