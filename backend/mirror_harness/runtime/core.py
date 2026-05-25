from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from ..knowledge.indexer import build_index, save_index
from ..knowledge.kb_exporter import export_knowledge_pack
from ..paths import HarnessPaths

# Keys whose value in `harness/.env` overrides the same key in template configs
# at sync time. This keeps backend Gateway and frontend SSR consistent without
# requiring the operator to edit two files in lockstep.
_ENV_OVERRIDE_KEYS_FOR_FRONTEND = ("PORTAL_AUTH_ENABLED",)


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _sync_extensions_config(paths: HarnessPaths) -> Path:
    src = paths.assets_config_dir / "extensions_config.json"
    dst = paths.upstream_deerflow / "extensions_config.json"
    raw = json.loads(src.read_text(encoding="utf-8"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst


def _read_env_value(env_file: Path, key: str) -> str | None:
    """Read a single ``KEY=value`` line from a dotenv-style file.

    Returns the raw value (with surrounding quotes stripped) or ``None`` if the
    key is absent or the file does not exist. Comment lines and blank lines are
    ignored.
    """
    if not env_file.exists():
        return None
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=(.*)$")
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = pattern.match(line)
        if match is None:
            continue
        value = match.group(1).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        return value
    return None


def _override_env_value(content: str, key: str, value: str) -> str:
    """Return ``content`` with ``key=value`` substituted; append if missing."""
    pattern = re.compile(rf"^(\s*){re.escape(key)}\s*=.*$", re.MULTILINE)
    if pattern.search(content):
        return pattern.sub(rf"\g<1>{key}={value}", content)
    if content and not content.endswith("\n"):
        content += "\n"
    return content + f"{key}={value}\n"


def _sync_frontend_env(paths: HarnessPaths) -> Path:
    """Sync ``frontend.env`` to ``deer-flow/frontend/.env``.

    Values listed in :data:`_ENV_OVERRIDE_KEYS_FOR_FRONTEND` are canonicalized
    from ``harness/.env`` so the frontend SSR and the backend Gateway always
    agree on Portal-auth state.
    """
    src = paths.assets_config_dir / "frontend.env"
    dst = paths.upstream_deerflow / "frontend" / ".env"
    content = src.read_text(encoding="utf-8")

    for key in _ENV_OVERRIDE_KEYS_FOR_FRONTEND:
        override = _read_env_value(paths.env_file, key)
        if override is not None:
            content = _override_env_value(content, key, override)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding="utf-8")
    return dst


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    shutil.copytree(src, dst, dirs_exist_ok=True)



def _sync_custom_skill(paths: HarnessPaths) -> Path:
    """Sync all custom skills into DeerFlow.

    Each skill source directory is the complete structure definition (static part).
    For mirrorsphere-knowledge: additionally inject the generated knowledge-pack.md.
    """
    last_dst: Path | None = None
    for src_skill_dir in sorted(paths.assets_custom_skills_dir.glob("*")):
        if not src_skill_dir.is_dir():
            continue
        dst_skill_dir = paths.upstream_custom_skills_dir / src_skill_dir.name
        if dst_skill_dir.exists():
            shutil.rmtree(dst_skill_dir)
        shutil.copytree(src_skill_dir, dst_skill_dir)
        last_dst = dst_skill_dir

    generated_dir = paths.upstream_custom_skills_dir / "mirrorsphere-knowledge" / "references" / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(paths.knowledge_pack_path, generated_dir / "knowledge-pack.md")

    if last_dst is None:
        return paths.upstream_custom_skills_dir / "mirrorsphere-knowledge"
    return last_dst


def _sync_agent_home(paths: HarnessPaths, deerflow_home: Path) -> Path:
    """Seed the legacy shared agent directory used as the read-only fallback.

    Per-user agent directories under ``users/{uid}/agents/mirrorsphere/`` are
    seeded at request time by ``mirror_harness.runtime.user_seed`` once Portal
    auth resolves the user, so no scan of ``users/`` is needed here.
    """
    agent_template_dir = paths.assets_custom_agents_dir / "mirrorsphere"
    agent_dir = deerflow_home / "agents" / "mirrorsphere"
    deerflow_home.mkdir(parents=True, exist_ok=True)
    _copy_tree(agent_template_dir, agent_dir)

    soul_path = deerflow_home / "SOUL.md"
    source_soul = agent_template_dir / "SOUL.md"
    if source_soul.exists():
        shutil.copy2(source_soul, soul_path)
    return agent_dir


def _sync_mirror_harness_package(paths: HarnessPaths) -> Path:
    """Copy mirror_harness package into DeerFlow backend so containers can import it.

    The DeerFlow dev container mounts ../backend/:/app/backend/ and sets
    PYTHONPATH=.  By placing mirror_harness under backend/ it becomes
    importable inside the container as ``mirror_harness.*``.
    """
    src = paths.src_dir / "mirror_harness"
    dst = paths.upstream_deerflow / "backend" / "mirror_harness"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return dst


def sync_upstream(paths: HarnessPaths) -> dict[str, str]:
    deerflow = paths.upstream_deerflow
    if not deerflow.exists():
        raise FileNotFoundError(f"DeerFlow upstream not found: {deerflow}")

    copied: dict[str, str] = {}
    mapping = {
        paths.assets_config_dir / "config.yaml": deerflow / "config.yaml",
    }
    for src, dst in mapping.items():
        _copy_file(src, dst)
        copied[str(src)] = str(dst)

    copied[str(paths.assets_config_dir / "frontend.env")] = str(_sync_frontend_env(paths))
    copied[str(paths.assets_config_dir / "extensions_config.json")] = str(_sync_extensions_config(paths))

    if paths.env_file.exists():
        _copy_file(paths.env_file, deerflow / ".env")
        copied[str(paths.env_file)] = str(deerflow / ".env")

    copied[str(paths.src_dir / "mirror_harness")] = str(_sync_mirror_harness_package(paths))

    return copied


def prepare_runtime(paths: HarnessPaths) -> dict[str, str]:
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.runtime_dir.mkdir(parents=True, exist_ok=True)
    paths.deerflow_home.mkdir(parents=True, exist_ok=True)
    paths.deerflow_dev_home.mkdir(parents=True, exist_ok=True)
    paths.runtime_reports_dir.mkdir(parents=True, exist_ok=True)
    paths.runtime_cache_dir.mkdir(parents=True, exist_ok=True)
    paths.runtime_evaluations_dir.mkdir(parents=True, exist_ok=True)
    paths.knowledge_dir.mkdir(parents=True, exist_ok=True)

    index = build_index(paths.mirrorsphere_root)
    save_index(index, paths.knowledge_index_path)
    export_knowledge_pack(index, paths.knowledge_pack_path)
    sync_upstream(paths)
    custom_skill_dir = _sync_custom_skill(paths)
    prod_agent_dir = _sync_agent_home(paths, paths.deerflow_home)
    dev_agent_dir = _sync_agent_home(paths, paths.deerflow_dev_home)

    manifest = {
        "harness_root": str(paths.root),
        "mirrorsphere_root": str(paths.mirrorsphere_root),
        "deerflow_root": str(paths.upstream_deerflow),
        "config_template_dir": str(paths.assets_config_dir),
        "custom_skills_dir": str(paths.assets_custom_skills_dir),
        "upstream_custom_skill_dir": str(custom_skill_dir),
        "deerflow_home": str(paths.deerflow_home),
        "deerflow_dev_home": str(paths.deerflow_dev_home),
        "deerflow_agent_dir": str(prod_agent_dir),
        "deerflow_dev_agent_dir": str(dev_agent_dir),
        "runtime_dir": str(paths.runtime_dir),
        "runtime_evaluations_dir": str(paths.runtime_evaluations_dir),
        "knowledge_index": str(paths.knowledge_index_path),
        "knowledge_pack": str(paths.knowledge_pack_path),
    }
    manifest_path = paths.runtime_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    env_path = paths.runtime_dir / "runtime.env"
    env_path.write_text(
        "\n".join(
            [
                f"HARNESS_ROOT={paths.root}",
                f"MIRRORSPHERE_ROOT={paths.mirrorsphere_root}",
                f"DEERFLOW_ROOT={paths.upstream_deerflow}",
                f"HARNESS_CUSTOM_SKILLS={paths.assets_custom_skills_dir}",
                f"DEER_FLOW_SKILLS_PATH={paths.upstream_skills_dir}",
                f"DEER_FLOW_HOME={paths.deerflow_home}",
                f"DEER_FLOW_DEV_HOME={paths.deerflow_dev_home}",
                f"HARNESS_EVALUATIONS_DIR={paths.evaluations_dir}",
                f"MIRROR_HARNESS_EVAL_REPORT_DIR={paths.runtime_evaluations_dir}",
                f"MIRROR_HARNESS_KNOWLEDGE_INDEX={paths.knowledge_index_path}",
                f"MIRROR_HARNESS_KNOWLEDGE_PACK={paths.knowledge_pack_path}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "manifest": str(manifest_path),
        "runtime_env": str(env_path),
        "deerflow_home": str(paths.deerflow_home),
        "deerflow_dev_home": str(paths.deerflow_dev_home),
        "custom_skill_dir": str(custom_skill_dir),
        "runtime_evaluations_dir": str(paths.runtime_evaluations_dir),
        "knowledge_index": str(paths.knowledge_index_path),
        "knowledge_pack": str(paths.knowledge_pack_path),
    }


def show_paths(paths: HarnessPaths) -> dict[str, str]:
    return {
        "root": str(paths.root),
        "upstreams_deerflow": str(paths.upstream_deerflow),
        "mirrorsphere_root": str(paths.mirrorsphere_root),
        "assets_config_dir": str(paths.assets_config_dir),
        "assets_custom_skills_dir": str(paths.assets_custom_skills_dir),
        "data_dir": str(paths.data_dir),
        "runtime_dir": str(paths.runtime_dir),
        "deerflow_home": str(paths.deerflow_home),
        "deerflow_dev_home": str(paths.deerflow_dev_home),
        "runtime_evaluations_dir": str(paths.runtime_evaluations_dir),
        "qa_eval_dataset_path": str(paths.qa_eval_dataset_path),
        "knowledge_index_path": str(paths.knowledge_index_path),
        "knowledge_pack_path": str(paths.knowledge_pack_path),
        "upstream_skills_dir": str(paths.upstream_skills_dir),
    }

