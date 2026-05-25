from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ChunkRecord:
    chunk_id: str
    path: str
    kind: str
    tags: list[str]
    start_line: int
    end_line: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class KnowledgeIndex:
    repo_root: str
    generated_at: str
    source_hash: str
    chunk_count: int
    chunks: list[ChunkRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "generated_at": self.generated_at,
            "source_hash": self.source_hash,
            "chunk_count": self.chunk_count,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "KnowledgeIndex":
        return cls(
            repo_root=raw["repo_root"],
            generated_at=raw["generated_at"],
            source_hash=raw.get("source_hash", ""),
            chunk_count=raw["chunk_count"],
            chunks=[ChunkRecord(**chunk) for chunk in raw["chunks"]],
        )


@dataclass(slots=True)
class RetrievalHit:
    chunk: ChunkRecord
    score: float
    matched_terms: list[str]


@dataclass(slots=True)
class AnswerResult:
    query: str
    answer: str
    evidence: list[RetrievalHit]

