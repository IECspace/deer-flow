from __future__ import annotations

from dataclasses import replace

from .models import Scenario, ScenarioStep, TestDesignModel
from .scope import ScopeConfig
from .utils import stable_id


def build_scenarios(
    model: TestDesignModel,
    scope: ScopeConfig,
    include_categories: set[str] | None = None,
    exclude_categories: set[str] | None = None,
) -> TestDesignModel:
    modules = []
    for m in model.modules:
        if include_categories is not None and m.category not in include_categories:
            modules.append(replace(m, scenarios=[]))
            continue
        if exclude_categories is not None and m.category in exclude_categories:
            modules.append(replace(m, scenarios=[]))
            continue
        if m.category not in {"functional", "nonfunctional"}:
            modules.append(replace(m, scenarios=[]))
            continue

        scenarios = []
        for r in m.requirements:
            base = f"{m.name}:{r.requirement_id}:{r.statement}"
            scenarios.append(_happy_path(r.requirement_id, r.statement, base))

            if len(scenarios) >= scope.max_cases_per_requirement:
                continue
            scenarios.append(_exception(r.requirement_id, r.statement, base))

            if scope.include_boundary and len(scenarios) < scope.max_cases_per_requirement:
                scenarios.append(_boundary(r.requirement_id, r.statement, base))
            if scope.include_permission and len(scenarios) < scope.max_cases_per_requirement:
                scenarios.append(_permission(r.requirement_id, r.statement, base))

        modules.append(replace(m, scenarios=scenarios))
    return replace(model, modules=modules)


def _happy_path(req_id: str, stmt: str, base: str) -> Scenario:
    sid = stable_id("S", f"happy:{base}")
    return Scenario(
        scenario_id=sid,
        name=f"{stmt} - 正常流程",
        type="happy_path",
        priority="P0",
        preconditions=[],
        steps=[
            ScenarioStep(action="进入功能入口/页面/接口", expected="入口可用"),
            ScenarioStep(action="按需求执行关键操作", expected="操作成功且结果符合验收标准"),
        ],
        assertions=["关键结果正确", "无错误提示/异常日志（如适用）"],
        tags=["functional", "workflow"],
        trace_requirement_ids=[req_id],
    )


def _exception(req_id: str, stmt: str, base: str) -> Scenario:
    sid = stable_id("S", f"ex:{base}")
    return Scenario(
        scenario_id=sid,
        name=f"{stmt} - 异常流程",
        type="exception",
        priority="P1",
        preconditions=[],
        steps=[
            ScenarioStep(action="构造一个典型失败条件（依赖不可用/参数非法/状态不允许）", expected="系统返回可判定的失败结果"),
        ],
        assertions=["错误码/提示符合规范", "不会产生脏数据或不可逆副作用"],
        risks=["异常处理规则未在 PRD 中明确，需确认错误码/提示/回滚策略"],
        tags=["functional", "exception"],
        trace_requirement_ids=[req_id],
    )


def _boundary(req_id: str, stmt: str, base: str) -> Scenario:
    sid = stable_id("S", f"bd:{base}")
    return Scenario(
        scenario_id=sid,
        name=f"{stmt} - 边界条件",
        type="boundary",
        priority="P2",
        preconditions=[],
        steps=[
            ScenarioStep(action="选择关键输入字段做边界值/空值/超长/特殊字符", expected="系统行为符合约束（通过/拒绝/截断/提示）"),
        ],
        assertions=["边界处理一致且可预测", "无崩溃/无未捕获异常"],
        tags=["boundary"],
        trace_requirement_ids=[req_id],
    )


def _permission(req_id: str, stmt: str, base: str) -> Scenario:
    sid = stable_id("S", f"perm:{base}")
    return Scenario(
        scenario_id=sid,
        name=f"{stmt} - 权限差异",
        type="permission",
        priority="P1",
        preconditions=["准备至少两类角色：有权限/无权限（或不同租户）"],
        steps=[
            ScenarioStep(action="使用无权限账号执行关键操作", expected="被拒绝且审计/提示符合要求"),
        ],
        assertions=["无越权访问", "拒绝路径可追踪（日志/审计如适用）"],
        risks=["角色/权限矩阵不清晰会影响用例准确性"],
        tags=["permission", "rbac"],
        trace_requirement_ids=[req_id],
    )

