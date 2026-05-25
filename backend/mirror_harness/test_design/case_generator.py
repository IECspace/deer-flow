from __future__ import annotations

from dataclasses import replace

from .models import Scenario, ScenarioStep, TestDesignModel
from .scope import ScopeConfig
from .utils import stable_id


def generate_cases(model: TestDesignModel, scope: ScopeConfig) -> TestDesignModel:
    modules = []
    for m in model.modules:
        scenarios = list(m.scenarios)
        if scope.include_nfr and m.category in {"functional", "nonfunctional"} and not any(s.type == "nfr" for s in scenarios):
            scenarios.append(_nfr_placeholder(module_name=m.name, requirement_ids=[r.requirement_id for r in m.requirements][:3]))
        modules.append(replace(m, scenarios=scenarios))
    return replace(model, modules=modules)


def _nfr_placeholder(module_name: str, requirement_ids: list[str]) -> Scenario:
    sid = stable_id("S", f"nfr:{module_name}")
    return Scenario(
        scenario_id=sid,
        name=f"{module_name} - 非功能需求（待确认）",
        type="nfr",
        priority="P2",
        preconditions=[],
        steps=[ScenarioStep(action="确认性能/稳定性/可观测性/安全等门槛", expected="形成可度量指标与检查点")],
        assertions=["指标有口径、有阈值、有采集方式"],
        risks=["PRD 未明确 NFR 指标时，该用例仅用于推动补齐信息"],
        tags=["nfr"],
        trace_requirement_ids=requirement_ids,
    )

