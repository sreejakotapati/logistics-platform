"""Audit router. Every tenant route is gated by `audit:read` and runs on the RLS tenant session, so
results are automatically scoped to the active org. The platform feed (org-NULL events) runs on the
identity session behind a platform permission.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_system_session
from app.modules.audit.repository import AuditFilters
from app.modules.audit.schemas import (
    AuditLogOut,
    AuditPage,
    AuditTimeline,
    RetentionPreview,
)
from app.modules.audit.service import AuditService, ExportService, RetentionService
from app.modules.rbac.deps import require_permission, require_platform_permission
from app.modules.tenancy.deps import get_tenant_session

router = APIRouter(prefix="/audit", tags=["audit"])

_READ = Depends(require_permission("audit:read"))


def _filters(
    action: str | None = Query(default=None),
    action_prefix: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: uuid.UUID | None = Query(default=None),
    actor_user_id: uuid.UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    q: str | None = Query(default=None, description="free-text search over action/entity/metadata"),
) -> AuditFilters:
    return AuditFilters(
        action=action, action_prefix=action_prefix, entity_type=entity_type, entity_id=entity_id,
        actor_user_id=actor_user_id, date_from=date_from, date_to=date_to, search=q,
    )


def _page(items, next_cursor, total) -> AuditPage:
    return AuditPage(items=[AuditLogOut(**i) for i in items], next_cursor=next_cursor, total=total)


# ===================================================================== query
@router.get("/logs", response_model=AuditPage, dependencies=[_READ])
async def query_logs(
    f: AuditFilters = Depends(_filters),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
    include_total: bool = Query(default=False),
    session: AsyncSession = Depends(get_tenant_session),
    settings: Settings = Depends(get_settings),
) -> AuditPage:
    items, nxt, total = await AuditService(session, settings).query(
        f, limit=limit, cursor=cursor, include_total=include_total
    )
    return _page(items, nxt, total)


@router.get("/search", response_model=AuditPage, dependencies=[_READ])
async def search_logs(
    q: str = Query(min_length=1),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
    session: AsyncSession = Depends(get_tenant_session),
    settings: Settings = Depends(get_settings),
) -> AuditPage:
    items, nxt, _ = await AuditService(session, settings).query(
        AuditFilters(search=q), limit=limit, cursor=cursor
    )
    return _page(items, nxt, None)


@router.get("/timeline", response_model=AuditTimeline, dependencies=[_READ])
async def timeline(
    f: AuditFilters = Depends(_filters),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
    session: AsyncSession = Depends(get_tenant_session),
    settings: Settings = Depends(get_settings),
) -> AuditTimeline:
    buckets, nxt = await AuditService(session, settings).timeline(f, limit=limit, cursor=cursor)
    return AuditTimeline(buckets=buckets, next_cursor=nxt)


# =========================================================== actor / entity
@router.get("/actors/{actor_user_id}", response_model=AuditPage, dependencies=[_READ])
async def actor_history(
    actor_user_id: uuid.UUID,
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
    session: AsyncSession = Depends(get_tenant_session),
    settings: Settings = Depends(get_settings),
) -> AuditPage:
    items, nxt, _ = await AuditService(session, settings).query(
        AuditFilters(actor_user_id=actor_user_id), limit=limit, cursor=cursor
    )
    return _page(items, nxt, None)


@router.get(
    "/entities/{entity_type}/{entity_id}", response_model=AuditPage, dependencies=[_READ]
)
async def entity_history(
    entity_type: str, entity_id: uuid.UUID,
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
    session: AsyncSession = Depends(get_tenant_session),
    settings: Settings = Depends(get_settings),
) -> AuditPage:
    # chronological (ascending) — the lifecycle of one entity
    items, nxt, _ = await AuditService(session, settings).query(
        AuditFilters(entity_type=entity_type, entity_id=entity_id),
        limit=limit, cursor=cursor, ascending=True,
    )
    return _page(items, nxt, None)


# ==================================================================== export
@router.get("/export", dependencies=[_READ])
async def export_logs(
    f: AuditFilters = Depends(_filters),
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    session: AsyncSession = Depends(get_tenant_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    body, media_type, count = await ExportService(session, settings).build(f, format)
    ext = "csv" if format == "csv" else "json"
    return Response(
        content=body, media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="audit-export.{ext}"',
            "X-Audit-Row-Count": str(count),
        },
    )


# ================================================================= retention
@router.get("/retention", response_model=RetentionPreview, dependencies=[_READ])
async def retention_preview(
    f: AuditFilters = Depends(_filters),
    session: AsyncSession = Depends(get_tenant_session),
    settings: Settings = Depends(get_settings),
) -> RetentionPreview:
    return RetentionPreview(**await RetentionService(session, settings).preview(f))


@router.get("/retention/archive", dependencies=[_READ])
async def retention_archive(
    format: str = Query(default="csv", pattern="^(csv|json)$"),
    session: AsyncSession = Depends(get_tenant_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    # Archival export of records past the retention window (cold-storage handoff; never deletes).
    cutoff = RetentionService(session, settings).cutoff()
    body, media_type, count = await ExportService(session, settings).build(
        AuditFilters(date_to=cutoff), format
    )
    ext = "csv" if format == "csv" else "json"
    return Response(
        content=body, media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="audit-archive.{ext}"',
            "X-Audit-Row-Count": str(count),
        },
    )


# ============================================== platform-scope audit feed
@router.get(
    "/platform/logs", response_model=AuditPage,
    dependencies=[Depends(require_platform_permission("org:provision"))],
)
async def platform_logs(
    f: AuditFilters = Depends(_filters),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> AuditPage:
    f.platform_only = True
    items, nxt, _ = await AuditService(session, settings).query(f, limit=limit, cursor=cursor)
    return _page(items, nxt, None)
