"""Read model over refresh-token families for session management. No new tables — the existing
`auth_refresh_tokens` rows already represent sessions (one active head per family).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshToken


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def active_for_user(self, user_id: uuid.UUID) -> list[RefreshToken]:
        stmt = (
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.rotated_at.is_(None),
                RefreshToken.expires_at > _now(),
            )
            .order_by(RefreshToken.issued_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def family_belongs_to(self, family_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(func.count()).select_from(RefreshToken).where(
            RefreshToken.family_id == family_id, RefreshToken.user_id == user_id
        )
        return int((await self.session.execute(stmt)).scalar_one()) > 0
