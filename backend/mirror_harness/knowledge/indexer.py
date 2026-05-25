from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import ChunkRecord, KnowledgeIndex
from .taxonomy import infer_kind, infer_tags, normalize_index_path, should_index


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _iter_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(repo_root.rglob("*")):
        rel = path.relative_to(repo_root)
        if path.is_file() and should_index(rel):
            files.append(path)
    return files


def compute_source_hash(repo_root: Path) -> str:
    digest = hashlib.sha256()
    for path in _iter_files(repo_root):
        rel = path.relative_to(repo_root)
        stat = path.stat()
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(str(stat.st_size).encode("utf-8"))
        digest.update(str(stat.st_mtime_ns).encode("utf-8"))
    return digest.hexdigest()


def _chunk_lines(text: str, max_chunk_lines: int) -> list[tuple[int, int, str]]:
    lines = text.splitlines()
    chunks: list[tuple[int, int, str]] = []
    if not lines:
        return [(1, 1, "")]
    for start in range(0, len(lines), max_chunk_lines):
        end = min(start + max_chunk_lines, len(lines))
        chunk_text = "\n".join(lines[start:end]).strip()
        if chunk_text:
            chunks.append((start + 1, end, chunk_text))
    return chunks


def build_index(repo_root: Path, max_chunk_lines: int = 80) -> KnowledgeIndex:
    files = _iter_files(repo_root)
    chunks: list[ChunkRecord] = []
    digest = hashlib.sha256()
    for file_path in files:
        rel = file_path.relative_to(repo_root)
        stat = file_path.stat()
        digest.update(rel.as_posix().encode("utf-8"))
        digest.update(str(stat.st_size).encode("utf-8"))
        digest.update(str(stat.st_mtime_ns).encode("utf-8"))
        text = _read_text(file_path)
        kind = infer_kind(rel)
        tags = infer_tags(rel, text)
        indexed_path = normalize_index_path(rel.as_posix())
        for idx, (start_line, end_line, chunk_text) in enumerate(_chunk_lines(text, max_chunk_lines), start=1):
            chunks.append(
                ChunkRecord(
                    chunk_id=f"{indexed_path}#{idx}",
                    path=indexed_path,
                    kind=kind,
                    tags=tags,
                    start_line=start_line,
                    end_line=end_line,
                    text=chunk_text,
                )
            )
    return KnowledgeIndex(
        repo_root=str(repo_root),
        generated_at=datetime.now(timezone.utc).isoformat(),
        source_hash=digest.hexdigest(),
        chunk_count=len(chunks),
        chunks=chunks,
    )


def save_index(index: KnowledgeIndex, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


def load_index(path: Path) -> KnowledgeIndex:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return KnowledgeIndex.from_dict(raw)

