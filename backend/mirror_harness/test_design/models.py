from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


Priority = Literal["P0", "P1", "P2"]
ScenarioType = Literal["happy_path", "exception", "boundary", "permission", "compat", "nfr"]


@dataclass(slots=True)
class SourceRef:
    source: str
    locator: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "locator": self.locator}


@dataclass(slots=True)
class GapQuestion:
    question_id: str
    question: str
    why_it_matters: str
    suggested_owner: str = "PM/Dev/QA"

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question": self.question,
            "why_it_matters": self.why_it_matters,
            "suggested_owner": self.suggested_owner,
        }


@dataclass(slots=True)
class NormalizedPRD:
    title: str
    text: str
    sources: list[SourceRef] = field(default_factory=list)
    sections: list[dict[str, Any]] = field(default_factory=list)  # lightweight for MVP
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "text": self.text,
            "sources": [s.to_dict() for s in self.sources],
            "sections": self.sections,
            "generated_at": self.generated_at,
        }


@dataclass(slots=True)
class DesignItem:
    requirement_id: str
    statement: str
    acceptance: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    nfr: list[str] = field(default_factory=list)
    trace: list[SourceRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.requirement_id,
            "statement": self.statement,
            "acceptance": self.acceptance,
            "constraints": self.constraints,
            "nfr": self.nfr,
            "trace": [t.to_dict() for t in self.trace],
        }


@dataclass(slots=True)
class ScenarioStep:
    action: str
    data: str = ""
    expected: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"action": self.action, "data": self.data, "expected": self.expected}


@dataclass(slots=True)
class Scenario:
    scenario_id: str
    name: str
    type: ScenarioType
    priority: Priority
    preconditions: list[str] = field(default_factory=list)
    steps: list[ScenarioStep] = field(default_factory=list)
    assertions: list[str] = field(default_factory=list)
    test_data: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    trace_requirement_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.scenario_id,
            "name": self.name,
            "type": self.type,
            "priority": self.priority,
            "preconditions": self.preconditions,
            "steps": [s.to_dict() for s in self.steps],
            "assertions": self.assertions,
            "test_data": self.test_data,
            "risks": self.risks,
            "tags": self.tags,
            "trace_requirement_ids": self.trace_requirement_ids,
        }


@dataclass(slots=True)
class DesignModule:
    module_id: str
    name: str
    category: str = "functional"  # functional | nonfunctional | analytics | rollout | risk | data
    requirements: list[DesignItem] = field(default_factory=list)
    scenarios: list[Scenario] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.module_id,
            "name": self.name,
            "category": self.category,
            "requirements": [r.to_dict() for r in self.requirements],
            "scenarios": [s.to_dict() for s in self.scenarios],
        }


@dataclass(slots=True)
class TestDesignModel:
    prd_id: str
    title: str
    version: str = ""
    source: str = ""
    actors: list[dict[str, Any]] = field(default_factory=list)
    modules: list[DesignModule] = field(default_factory=list)
    gaps: list[GapQuestion] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=utc_now_iso)
    schema_version: str = "v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "prd": {"id": self.prd_id, "title": self.title, "version": self.version, "source": self.source},
            "actors": self.actors,
            "modules": [m.to_dict() for m in self.modules],
            "gaps": [g.to_dict() for g in self.gaps],
            "assumptions": self.assumptions,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "TestDesignModel":
        prd = raw.get("prd", {})
        return cls(
            prd_id=prd.get("id", ""),
            title=prd.get("title", ""),
            version=prd.get("version", ""),
            source=prd.get("source", ""),
            actors=raw.get("actors", []),
            modules=[
                DesignModule(
                    module_id=m.get("id", ""),
                    name=m.get("name", ""),
                    category=m.get("category", "functional"),
                    requirements=[
                        DesignItem(
                            requirement_id=r.get("id", ""),
                            statement=r.get("statement", ""),
                            acceptance=r.get("acceptance", []),
                            constraints=r.get("constraints", []),
                            nfr=r.get("nfr", []),
                            trace=[SourceRef(source=t.get("source", ""), locator=t.get("locator", "")) for t in r.get("trace", [])],
                        )
                        for r in m.get("requirements", [])
                    ],
                    scenarios=[
                        Scenario(
                            scenario_id=s.get("id", ""),
                            name=s.get("name", ""),
                            type=s.get("type", "happy_path"),
                            priority=s.get("priority", "P1"),
                            preconditions=s.get("preconditions", []),
                            steps=[ScenarioStep(action=st.get("action", ""), data=st.get("data", ""), expected=st.get("expected", "")) for st in s.get("steps", [])],
                            assertions=s.get("assertions", []),
                            test_data=s.get("test_data", []),
                            risks=s.get("risks", []),
                            tags=s.get("tags", []),
                            trace_requirement_ids=s.get("trace_requirement_ids", []),
                        )
                        for s in m.get("scenarios", [])
                    ],
                )
                for m in raw.get("modules", [])
            ],
            gaps=[
                GapQuestion(
                    question_id=g.get("question_id", ""),
                    question=g.get("question", ""),
                    why_it_matters=g.get("why_it_matters", ""),
                    suggested_owner=g.get("suggested_owner", "PM/Dev/QA"),
                )
                for g in raw.get("gaps", [])
            ],
            assumptions=raw.get("assumptions", []),
            generated_at=raw.get("generated_at", utc_now_iso()),
            schema_version=raw.get("schema_version", "v1"),
        )

