"""Repository layer for Users & Organizations.

Tenant repositories operate on the RLS-enforced tenant session (org context already set); identity
operations (invitation lookup by token, accept) run on the privileged session. No business rules here.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import (
    Invitation,
    Organization,
    User,
    UserOrganization,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_current(self) -> Organization | None:
        # Under RLS exactly the active org is visible.
        return (await self.session.execute(select(Organization).limit(1))).scalar_one_or_none()

    async def update_profile(self, org: Organization, values: dict) -> Organization:
        for key, val in values.items():
            setattr(org, key, val)
        org.version = org.version + 1 if org.version else 1
        await self.session.flush()
        return org

    async def update_settings(self, org: Organization, patch: dict) -> Organization:
        merged = dict(org.settings or {})
        merged.update(patch)
        org.settings = merged
        org.version = org.version + 1 if org.version else 1
        await self.session.flush()
        return org

    async def close(self, org: Organization) -> Organization:
        org.status = "closed"
        org.deleted_at = _now()
        await self.session.flush()
        return org


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_members(self) -> list[tuple[UserOrganization, User]]:
        stmt = (
            select(UserOrganization, User)
            .join(User, User.id == UserOrganization.user_id)
            .where(UserOrganization.deleted_at.is_(None))
            .order_by(UserOrganization.is_primary.desc(), User.email.asc())
        )
        return list((await self.session.execute(stmt)).tuples().all())

    async def get_member(self, user_id: uuid.UUID) -> tuple[UserOrganization, User] | None:
        stmt = (
            select(UserOrganization, User)
            .join(User, User.id == UserOrganization.user_id)
            .where(UserOrganization.user_id == user_id, UserOrganization.deleted_at.is_(None))
        )
        return (await self.session.execute(stmt)).tuples().first()

    async def get_membership(self, user_id: uuid.UUID) -> UserOrganization | None:
        stmt = select(UserOrganization).where(
            UserOrganization.user_id == user_id, UserOrganization.deleted_at.is_(None)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def update_status(self, membership: UserOrganization, status: str) -> None:
        membership.status = status
        await self.session.flush()

    async def soft_remove(self, membership: UserOrganization) -> None:
        membership.deleted_at = _now()
        membership.status = "removed"
        await self.session.flush()

    async def active_member_count(self) -> int:
        stmt = select(func.count()).select_from(UserOrganization).where(
            UserOrganization.deleted_at.is_(None), UserOrganization.status == "active"
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def exists_active(self, user_id: uuid.UUID, organization_id: uuid.UUID) -> bool:
        stmt = select(func.count()).select_from(UserOrganization).where(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == organization_id,
            UserOrganization.deleted_at.is_(None),
        )
        return int((await self.session.execute(stmt)).scalar_one()) > 0

    async def create(
        self, *, user_id: uuid.UUID, organization_id: uuid.UUID, is_primary: bool,
        status: str = "active", invited_by: uuid.UUID | None = None,
    ) -> UserOrganization:
        m = UserOrganization(
            user_id=user_id, organization_id=organization_id, is_primary=is_primary,
            status=status, invited_by=invited_by,
        )
        self.session.add(m)
        await self.session.flush()
        return m


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, *, organization_id: uuid.UUID, email: str, role_id: uuid.UUID | None,
        invited_by: uuid.UUID | None, token_hash: str, expires_at: datetime,
    ) -> Invitation:
        inv = Invitation(
            organization_id=organization_id, email=email.lower(), role_id=role_id,
            invited_by=invited_by, token_hash=token_hash, expires_at=expires_at,
            created_by=invited_by,
        )
        self.session.add(inv)
        await self.session.flush()
        return inv

    async def list_pending(self) -> list[Invitation]:
        stmt = (
            select(Invitation)
            .where(Invitation.deleted_at.is_(None))
            .order_by(Invitation.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_by_id(self, invitation_id: uuid.UUID) -> Invitation | None:
        stmt = select(Invitation).where(
            Invitation.id == invitation_id, Invitation.deleted_at.is_(None)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def pending_for_email(self, organization_id: uuid.UUID, email: str) -> Invitation | None:
        stmt = select(Invitation).where(
            Invitation.organization_id == organization_id,
            func.lower(Invitation.email) == email.lower(),
            Invitation.status == "pending",
            Invitation.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        stmt = select(Invitation).where(Invitation.token_hash == token_hash)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def revoke(self, inv: Invitation) -> None:
        inv.status = "revoked"
        inv.deleted_at = _now()
        await self.session.flush()

    async def mark_accepted(self, inv: Invitation, user_id: uuid.UUID) -> None:
        inv.status = "accepted"
        inv.accepted_at = _now()
        inv.accepted_user_id = user_id
        await self.session.flush()


class UserProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        return (
            await self.session.execute(
                select(User).where(User.id == user_id, User.deleted_at.is_(None))
            )
        ).scalar_one_or_none()

    async def update_profile(self, user: User, full_name: str) -> None:
        user.full_name = full_name
        await self.session.flush()

    async def get_by_email(self, email: str) -> User | None:
        return (
            await self.session.execute(
                select(User).where(func.lower(User.email) == email.lower(), User.deleted_at.is_(None))
            )
        ).scalar_one_or_none()
