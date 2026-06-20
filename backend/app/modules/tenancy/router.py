"""Tenancy router — a demonstrator tenant route that proves the wiring end to end.

`GET /tenancy/context` runs through the tenant guard, so it only succeeds for an active member of the
active org, and any tenant query it runs sees ONLY that org's rows (RLS). Full organization management
is S2-T4; this route exists to validate context injection + the guard.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tenancy.context import TenantContext
from app.modules.tenancy.deps import get_tenant_context, get_tenant_session

router = APIRouter(prefix="/tenancy", tags=["tenancy"])


@router.get("/context")
async def current_context(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_tenant_session),
) -> dict:
    # Under RLS this returns exactly the active organization — proof the context is wired.
    rows = (
        await session.execute(text("SELECT id, name, slug FROM organizations ORDER BY name"))
    ).all()
    return {
        "user_id": str(ctx.user_id),
        "active_organization_id": str(ctx.organization_id),
        "visible_organizations": [
            {"id": str(r[0]), "name": r[1], "slug": r[2]} for r in rows
        ],
    }
