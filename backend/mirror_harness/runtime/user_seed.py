"""Seed per-user agent directories with the mirrorsphere config on first auth.

Problem
-------
DeerFlow's memory writer creates ``{deerflow_home}/users/{uid}/agents/{name}/memory.json``
after a successful chat. ``resolve_agent_dir`` then treats "directory exists"
as "user already owns this agent", so subsequent requests resolve to that
directory and crash when ``load_agent_config`` cannot find ``config.yaml``.

Fix
---
At the moment :class:`PortalAuthMiddleware` resolves a Portal user to a
DeerFlow user, call :func:`ensure_user_agent_seeded` to idempotently copy the
mirrorsphere agent template (``config.yaml`` + ``SOUL.md``) into the
per-user directory. Operation is best-effort: any I/O failure is logged and
swallowed so storage hiccups never break the auth path.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

# Custom agents to seed for every authenticated user. Must stay in sync with
# the templates shipped under ``mirror_harness/assets/custom/agents/``.
_SEED_AGENTS: tuple[str, ...] = ("mirrorsphere",)


def _template_root() -> Path:
    """Return the harness-shipped custom agents directory.

    The mirror_harness package is copied into ``backend/mirror_harness/`` by
    ``prepare-runtime`` so this path resolves identically inside and outside
    the DeerFlow container.
    """
    # __file__ = .../mirror_harness/runtime/user_seed.py
    return Path(__file__).resolve().parent.parent / "assets" / "custom" / "agents"


def _seed_dir(template_dir: Path, target_dir: Path) -> None:
    """Copy files from ``template_dir`` into ``target_dir`` without overwriting.

    Recurses into subdirectories. Existing files in ``target_dir`` (e.g.
    ``memory.json`` written by DeerFlow, or user-customized ``config.yaml``)
    are left untouched.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    for src in template_dir.iterdir():
        dst = target_dir / src.name
        if src.is_dir():
            _seed_dir(src, dst)
        elif src.is_file() and not dst.exists():
            shutil.copy2(src, dst)


def ensure_user_agent_seeded(user_id: str) -> None:
    """Idempotently seed per-user agent dirs for the given user.

    Called from :class:`PortalAuthMiddleware` after successful Portal auth.
    Cheap when already seeded (one ``stat`` per configured agent) and silent
    on failure.
    """
    if not user_id:
        return

    try:
        from deerflow.config.paths import get_paths
    except ImportError:
        logger.debug("deerflow.config.paths unavailable; user_seed is a no-op")
        return

    try:
        paths = get_paths()
    except Exception:
        logger.warning("user_seed: get_paths() failed", exc_info=True)
        return

    template_root = _template_root()
    if not template_root.is_dir():
        logger.warning("user_seed: template root missing at %s", template_root)
        return

    for agent_name in _SEED_AGENTS:
        template_dir = template_root / agent_name
        if not template_dir.is_dir() or not (template_dir / "config.yaml").exists():
            continue

        try:
            user_agent_dir = paths.user_agent_dir(user_id, agent_name)
        except Exception:
            logger.warning(
                "user_seed: failed to resolve user_agent_dir for %s/%s",
                user_id,
                agent_name,
                exc_info=True,
            )
            continue

        if (user_agent_dir / "config.yaml").exists():
            continue

        try:
            _seed_dir(template_dir, user_agent_dir)
            logger.info(
                "user_seed: seeded agent %s for user %s at %s",
                agent_name,
                user_id,
                user_agent_dir,
            )
        except Exception:
            logger.warning(
                "user_seed: failed to seed %s for user %s at %s",
                agent_name,
                user_id,
                user_agent_dir,
                exc_info=True,
            )
