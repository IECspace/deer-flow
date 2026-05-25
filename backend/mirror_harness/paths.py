from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HarnessPaths:
    root: Path
    mirrorsphere_root: Path
    upstream_deerflow: Path
    src_dir: Path
    package_dir: Path
    assets_dir: Path
    assets_config_dir: Path
    assets_custom_dir: Path
    assets_custom_agents_dir: Path
    assets_custom_skills_dir: Path
    data_dir: Path
    runtime_dir: Path
    deerflow_home: Path
    deerflow_dev_home: Path
    runtime_reports_dir: Path
    runtime_cache_dir: Path
    runtime_evaluations_dir: Path
    knowledge_dir: Path
    knowledge_index_path: Path
    knowledge_pack_path: Path
    evaluations_dir: Path
    qa_eval_dataset_path: Path
    upstream_skills_dir: Path
    upstream_custom_skills_dir: Path
    env_file: Path

    @classmethod
    def detect(cls) -> "HarnessPaths":
        package_dir = Path(__file__).resolve().parent
        src_dir = package_dir.parent
        root = src_dir.parent
        mirrorsphere_root = root.parent
        assets_dir = package_dir / "assets"
        data_dir = root / "data"
        runtime_dir = data_dir / "runtime"
        knowledge_dir = data_dir / "knowledge"
        evaluations_dir = package_dir / "evals" / "datasets"
        return cls(
            root=root,
            mirrorsphere_root=mirrorsphere_root,
            upstream_deerflow=root / "upstreams" / "deer-flow",
            src_dir=src_dir,
            package_dir=package_dir,
            assets_dir=assets_dir,
            assets_config_dir=assets_dir / "config",
            assets_custom_dir=assets_dir / "custom",
            assets_custom_agents_dir=assets_dir / "custom" / "agents",
            assets_custom_skills_dir=assets_dir / "custom" / "skills",
            data_dir=data_dir,
            runtime_dir=runtime_dir,
            deerflow_home=data_dir / ".deer-flow",
            deerflow_dev_home=root / "upstreams" / "deer-flow" / "backend" / ".deer-flow",
            runtime_reports_dir=runtime_dir / "reports",
            runtime_cache_dir=runtime_dir / "cache",
            runtime_evaluations_dir=runtime_dir / "evaluations",
            knowledge_dir=knowledge_dir,
            knowledge_index_path=knowledge_dir / "mirrorsphere-index.json",
            knowledge_pack_path=knowledge_dir / "mirrorsphere-knowledge-pack.md",
            evaluations_dir=evaluations_dir,
            qa_eval_dataset_path=evaluations_dir / "knowledge_qa_dataset.json",
            upstream_skills_dir=root / "upstreams" / "deer-flow" / "skills",
            upstream_custom_skills_dir=root / "upstreams" / "deer-flow" / "skills" / "custom",
            env_file=root / ".env",
        )
