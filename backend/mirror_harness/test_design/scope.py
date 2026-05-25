from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CoverageProfile = Literal["minimal", "standard", "strict"]


@dataclass(frozen=True)
class ScopeConfig:
    profile: CoverageProfile = "standard"
    include_nfr: bool = True
    include_permission: bool = True
    include_boundary: bool = True
    max_cases_per_requirement: int = 4


def scope_from_profile(profile: CoverageProfile) -> ScopeConfig:
    if profile == "minimal":
        return ScopeConfig(profile=profile, include_nfr=False, include_permission=False, include_boundary=False, max_cases_per_requirement=2)
    if profile == "strict":
        return ScopeConfig(profile=profile, include_nfr=True, include_permission=True, include_boundary=True, max_cases_per_requirement=6)
    return ScopeConfig(profile=profile)

