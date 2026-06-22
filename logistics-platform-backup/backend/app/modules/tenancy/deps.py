"""Tenant dependencies — the tenant route guard and database context injection.

`get_tenant_session` is the single gate every tenant route uses. It (1) sets the RLS context
(`app.current_org_id`) from the signed active-org claim, (2) validates that the caller is an active
member of that org — using the RLS plane itself — and (3) yields the request-scoped, RLS-enforced
session inside one transaction. The active org is taken ONLY from the JWT.
"""
from __future__ import annotations

import uuid
from typing import AsyncIterator

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_sessionmaker
from app.modules.tenancy.context import TenantContext


def get_access_claims(request: Request) -> dict:
    claims = getattr(request.state, "auth_claims", None)
    if not claims:
        raise UnauthorizedError("Missing or invalid access token")
    return claims


def get_active_organization_id(claims: dict = Depends(get_access_claims)) -> uuid.UUID:
    org = claims.get("org")
    if not org:
        raise ForbiddenError("No active organization in the current session")
    return uuid.UUID(org)


def get_tenant_context(claims: dict = Depends(get_access_claims)) -> TenantContext:
    org = claims.get("org")
    if not org:
        raise ForbiddenError("No active organization in the current session")
    return TenantContext(user_id=uuid.UUID(claims["sub"]), organization_id=uuid.UUID(org))


async def get_tenant_session(
    claims: dict = Depends(get_access_claims),
) -> AsyncIterator[AsyncSession]:
    """RLS-enforced session with org context set and membership validated. Tenant routes depend on this."""
    org = claims.get("org")
    if not org:
        raise ForbiddenError("No active organization in the current session")
    user_id = claims["sub"]

    async with get_sessionmaker()() as session:
        # 1) Database context injection — transaction-local, read by app.current_org_id().
        await session.execute(
            text("SELECT set_config('app.current_org_id', :oid, true)"), {"oid": str(org)}
        )
        # 2) Membership validation, enforced through RLS itself: under this org context the row is
        #    visible only if the caller holds an active, non-deleted membership in THIS org.
        member = await session.scalar(
            text(
                "SELECT 1 FROM user_organizations "
                "WHERE user_id = :uid AND status = 'active' AND deleted_at IS NULL LIMIT 1"
            ),
            {"uid": user_id},
        )
        if not member:
            raise ForbiddenError("You are not an active member of the active organization")
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
