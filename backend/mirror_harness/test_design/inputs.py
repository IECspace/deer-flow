from __future__ import annotations

from pathlib import Path

from .models import NormalizedPRD, SourceRef
from .utils import first_non_empty_line, normalize_whitespace


def load_prd_text(inputs: list[Path]) -> NormalizedPRD:
    """Load PRD from one or more files.

    Behavior:
    - Treat everything as text, attempting UTF-8 decode
    - If `markitdown` is available, use it for non-md extensions
    """

    combined_parts: list[str] = []
    sources: list[SourceRef] = []

    for p in inputs:
        sources.append(SourceRef(source=str(p)))
        ext = p.suffix.lower()
        if ext in {".md", ".markdown", ".txt"}:
            combined_parts.append(_read_text(p))
            continue
        extracted = _try_markitdown(p)
        combined_parts.append(extracted if extracted else _read_text(p))

    combined = normalize_whitespace("\n\n".join(part for part in combined_parts if part.strip()))
    title = _infer_title(combined, inputs)
    return NormalizedPRD(title=title, text=combined, sources=sources)


def _infer_title(text: str, inputs: list[Path]) -> str:
    for line in text.splitlines()[:50]:
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()[:120] or (inputs[0].stem if inputs else "PRD")
    first = first_non_empty_line(text)
    if first and len(first) <= 120:
        return first
    return inputs[0].stem if inputs else "PRD"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _try_markitdown(path: Path) -> str | None:
    try:
        from markitdown import MarkItDown  # type: ignore
    except Exception:
        return None
    try:
        md = MarkItDown()
        result = md.convert(str(path))
        text = getattr(result, "text_content", None) or getattr(result, "text", None) or str(result)
        return normalize_whitespace(text)
    except Exception:
        return None

