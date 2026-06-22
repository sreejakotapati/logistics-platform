"""Audit repository — read-only access with keyset pagination and a streaming export iterator.

Tenancy is enforced by RLS on the tenant session (the active org is the only org visible). The platform
variant runs on the privileged session and filters `organization_id IS NULL` for platform-scope events.
No write methods exist here.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator

from sqlalchemy import Text, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.modules.audit.models import AuditLog


@dataclass
class AuditFilters:
    action: str | None = None
    action_prefix: str | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    actor_user_id: uuid.UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    search: str | None = None
    platform_only: bool = False


def _conditions(f: AuditFilters) -> list[ColumnElement[bool]]:
    conds: list[ColumnElement[bool]] = []
    if f.platform_only:
        conds.append(AuditLog.organization_id.is_(None))
    if f.action:
        conds.append(AuditLog.action == f.action)
    if f.action_prefix:
        conds.append(AuditLog.action.like(f"{f.action_prefix}%"))
    if f.entity_type:
        conds.append(AuditLog.entity_type == f.entity_type)
    if f.entity_id:
        conds.append(AuditLog.entity_id == f.entity_id)
    if f.actor_user_id:
        conds.append(AuditLog.actor_user_id == f.actor_user_id)
    if f.date_from:
        conds.append(AuditLog.created_at >= f.date_from)
    if f.date_to:
        conds.append(AuditLog.created_at <= f.date_to)
    if f.search:
        like = f"%{f.search}%"
        conds.append(
            or_(
                AuditLog.action.ilike(like),
                AuditLog.entity_type.ilike(like),
                cast(AuditLog.meta, Text).ilike(like),
            )
        )
    return conds


def _keyset(created_at: datetime, row_id: uuid.UUID, ascending: bool) -> ColumnElement[bool]:
    if ascending:
        return or_(
            AuditLog.created_at > created_at,
            and_(AuditLog.created_at == created_at, AuditLog.id > row_id),
        )
    return or_(
        AuditLog.created_at < created_at,
        and_(AuditLog.created_at == created_at, AuditLog.id < row_id),
    )


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def page(
        self, f: AuditFilters, *, limit: int, cursor: tuple[datetime, uuid.UUID] | None,
        ascending: bool = False,
    ) -> tuple[list[AuditLog], bool]:
        conds = _conditions(f)
        if cursor:
            conds.append(_keyset(cursor[0], cursor[1], ascending))
        order = (
            (AuditLog.created_at.asc(), AuditLog.id.asc())
            if ascending
            else (AuditLog.created_at.desc(), AuditLog.id.desc())
        )
        stmt = select(AuditLog).where(*conds).order_by(*order).limit(limit + 1)
        rows = list((await self.session.execute(stmt)).scalars().all())
        has_more = len(rows) > limit
        return rows[:limit], has_more

    async def count(self, f: AuditFilters) -> int:
        stmt = select(func.count()).select_from(AuditLog).where(*_conditions(f))
        return int((await self.session.execute(stmt)).scalar_one())

    async def bounds(self, f: AuditFilters) -> tuple[datetime | None, datetime | None]:
        stmt = select(func.min(AuditLog.created_at), func.max(AuditLog.created_at)).where(*_conditions(f))
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1]) if row else (None, None)

    async def iter_export(
        self, f: AuditFilters, *, chunk: int = 1000, max_rows: int
    ) -> AsyncIterator[AuditLog]:
        """Keyset-stream matching rows oldest-first, bounded by max_rows. Worker/background friendly."""
        cursor: tuple[datetime, uuid.UUID] | None = None
        emitted = 0
        while emitted < max_rows:
            take = min(chunk, max_rows - emitted)
            rows, _ = await self.page(f, limit=take, cursor=cursor, ascending=True)
            if not rows:
                break
            for r in rows:
                yield r
                emitted += 1
            cursor = (rows[-1].created_at, rows[-1].id)
            if len(rows) < take:
                break
