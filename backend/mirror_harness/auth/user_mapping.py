"""Map Portal users to DeerFlow users (auto-create on first visit)."""

from __future__ import annotations

import logging
from uuid import uuid4

from .portal_provider import PortalUserInfo

logger = logging.getLogger(__name__)

_OAUTH_PROVIDER = "portal"


class PortalUserMapping:
    """Maps Portal uid -> DeerFlow User using oauth_provider/oauth_id fields."""

    async def get_or_create_user(self, portal_info: PortalUserInfo):
        """Find existing DeerFlow user by Portal uid, or create one.

        Returns a DeerFlow User object compatible with request.state.user.
        """
        from app.gateway.auth.models import User
        from app.gateway.deps import get_local_provider

        provider = get_local_provider()
        repo = provider._repo

        user = await repo.get_user_by_oauth(_OAUTH_PROVIDER, portal_info.uid)
        if user is not None:
            return user

        email = f"portal_{portal_info.uid}@mirrorsphere.io"
        new_user = User(
            id=uuid4(),
            email=email,
            password_hash=None,
            system_role="user",
            oauth_provider=_OAUTH_PROVIDER,
            oauth_id=portal_info.uid,
        )
        try:
            user = await repo.create_user(new_user)
            logger.info("Created DeerFlow user for Portal uid=%s", portal_info.uid)
        except ValueError:
            user = await repo.get_user_by_oauth(_OAUTH_PROVIDER, portal_info.uid)
            if user is None:
                logger.error("Failed to create or find user for Portal uid=%s", portal_info.uid)
        return user
