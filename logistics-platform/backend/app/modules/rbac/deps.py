"""Authorization dependencies.

`require_permission(key)` is the gate every protected tenant route declares. It resolves the caller's
effective permissions (cache → DB) for the active org and enforces the required key — it never inspects
role names. `require_platform_permission(key)` does the same against platform scope (Super Admin).
"""
from __future__ import annotations

import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.redis import get_redis
from app.db.session import get_system_session
from app.modules.rbac.service import RBACService
from app.modules.tenancy.deps import get_access_claims


def _service(session: AsyncSession, redis, settings: Settings) -> RBACService:
    return RBACService(session, redis, settings)


def require_permission(permission: str):
    """Dependency factory — enforces an org-scoped permission for the active org."""

    async def _checker(
        claims: dict = Depends(get_access_claims),
        session: AsyncSession = Depends(get_system_session),
        redis=Depends(get_redis),
        settings: Settings = Depends(get_settings),
    ) -> None:
        org = claims.get("org")
        if not org:
            raise ForbiddenError("No active organization in the current session")
        perms = await _service(session, redis, settings).effective_permissions(claims["sub"], org)
        if permission not in perms:
            raise ForbiddenError(f"Missing required permission: {permission}")

    return _checker


def require_platform_permission(permission: str):
    """Dependency factory — enforces a platform-scoped permission (Super Admin). Returns the user id."""

    async def _checker(
        claims: dict = Depends(get_access_claims),
        session: AsyncSession = Depends(get_system_session),
        redis=Depends(get_redis),
        settings: Settings = Depends(get_settings),
    ) -> uuid.UUID:
        perms = await _service(session, redis, settings).platform_permissions(claims["sub"])
        if permission not in perms:
            raise ForbiddenError(f"Missing required platform permission: {permission}")
        return uuid.UUID(claims["sub"])

    return _checker


async def get_effective_permissions(
    claims: dict = Depends(get_access_claims),
    session: AsyncSession = Depends(get_system_session),
    redis=Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> list[str]:
    org = claims.get("org")
    if not org:
        raise ForbiddenError("No active organization in the current session")
    return sorted(await _service(session, redis, settings).effective_permissions(claims["sub"], org))
