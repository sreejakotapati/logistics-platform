"""Session management — list and revoke a user's active sessions (refresh-token families).

Every revocation is audited as a security event. Runs on the identity (system) session.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import NotFoundError
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.security.audit import write_security_event
from app.modules.security.repository import SessionRepository


@dataclass
class SessionView:
    family_id: uuid.UUID
    issued_at: str
    expires_at: str
    ip_address: str | None
    user_agent: str | None
    active_organization_id: uuid.UUID | None
    current: bool


class SessionService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repo = SessionRepository(session)
        self.refresh = RefreshTokenRepository(session)

    async def list_sessions(
        self, user_id: uuid.UUID, current_family_id: uuid.UUID | None
    ) -> list[SessionView]:
        rows = await self.repo.active_for_user(user_id)
        return [
            SessionView(
                family_id=r.family_id,
                issued_at=r.issued_at.isoformat(),
                expires_at=r.expires_at.isoformat(),
                ip_address=r.ip_address,
                user_agent=r.user_agent,
                active_organization_id=r.active_organization_id,
                current=(r.family_id == current_family_id),
            )
            for r in rows
        ]

    async def revoke_session(
        self, user_id: uuid.UUID, family_id: uuid.UUID, *, ip: str | None = None
    ) -> None:
        if not await self.repo.family_belongs_to(family_id, user_id):
            raise NotFoundError("Session not found")
        await self.refresh.revoke_family(family_id, reason="user_revoked")
        await write_security_event(
            self.session, action="security.session_revoked", actor_id=user_id,
            entity_type="session", entity_id=family_id, metadata={"mode": "single"}, ip=ip,
        )
        await self.session.commit()

    async def revoke_other_sessions(
        self, user_id: uuid.UUID, current_family_id: uuid.UUID | None, *, ip: str | None = None
    ) -> int:
        rows = await self.repo.active_for_user(user_id)
        revoked = 0
        for r in rows:
            if r.family_id != current_family_id:
                await self.refresh.revoke_family(r.family_id, reason="user_revoked_others")
                revoked += 1
        await write_security_event(
            self.session, action="security.sessions_revoked_others", actor_id=user_id,
            entity_type="session", metadata={"revoked": revoked}, ip=ip,
        )
        await self.session.commit()
        return revoked

    async def enforce_max_concurrent(self, user_id: uuid.UUID) -> int:
        """Cap active families at session_max_concurrent (0 = unlimited). Revokes the oldest beyond the
        cap. Returns the count revoked. Caller commits."""
        cap = self.settings.session_max_concurrent
        if cap <= 0:
            return 0
        rows = await self.repo.active_for_user(user_id)  # newest first
        excess = rows[cap:]
        for r in excess:
            await self.refresh.revoke_family(r.family_id, reason="max_concurrent")
        if excess:
            await write_security_event(
                self.session, action="security.session_evicted", actor_id=user_id,
                entity_type="session", metadata={"revoked": len(excess), "cap": cap},
            )
        return len(excess)
