"""Repository layer for the auth/identity plane.

All methods take the identity-plane session (BYPASSRLS) supplied by the service. They contain no
business rules — only data access.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import (
    AuthToken,
    Organization,
    RefreshToken,
    Role,
    User,
    UserOrganization,
    UserOrganizationRole,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(
            func.lower(User.email) == email.lower(), User.deleted_at.is_(None)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(
        self, *, email: str, password_hash: str | None, full_name: str, status: str
    ) -> User:
        user = User(
            email=email, password_hash=password_hash, full_name=full_name, status=status
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def set_password(self, user_id: uuid.UUID, password_hash: str) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(password_hash=password_hash, status="active")
        )

    async def mark_email_verified(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(email_verified_at=_now())
        )


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, name: str, slug: str) -> Organization:
        org = Organization(name=name, slug=slug)
        self.session.add(org)
        await self.session.flush()
        return org


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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

    async def list_for_user(self, user_id: uuid.UUID) -> list[tuple[UserOrganization, Organization]]:
        stmt = (
            select(UserOrganization, Organization)
            .join(Organization, Organization.id == UserOrganization.organization_id)
            .where(UserOrganization.user_id == user_id, UserOrganization.deleted_at.is_(None))
            .order_by(UserOrganization.is_primary.desc(), Organization.name.asc())
        )
        return list((await self.session.execute(stmt)).tuples().all())

    async def get_primary(self, user_id: uuid.UUID) -> UserOrganization | None:
        stmt = (
            select(UserOrganization)
            .where(
                UserOrganization.user_id == user_id,
                UserOrganization.deleted_at.is_(None),
                UserOrganization.status == "active",
            )
            .order_by(UserOrganization.is_primary.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_active(
        self, user_id: uuid.UUID, organization_id: uuid.UUID
    ) -> UserOrganization | None:
        stmt = select(UserOrganization).where(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == organization_id,
            UserOrganization.status == "active",
            UserOrganization.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def system_role_id(self, name: str) -> uuid.UUID | None:
        stmt = select(Role.id).where(
            Role.organization_id.is_(None), func.lower(Role.name) == name.lower()
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()


class UserOrganizationRoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def assign(
        self, *, user_organization_id: uuid.UUID, role_id: uuid.UUID, organization_id: uuid.UUID
    ) -> None:
        self.session.add(
            UserOrganizationRole(
                user_organization_id=user_organization_id,
                role_id=role_id,
                organization_id=organization_id,
            )
        )
        await self.session.flush()


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, *, user_id: uuid.UUID, family_id: uuid.UUID, token_hash: str, expires_at: datetime,
        ip: str | None, user_agent: str | None, active_organization_id: uuid.UUID | None = None,
    ) -> RefreshToken:
        rec = RefreshToken(
            user_id=user_id, family_id=family_id, token_hash=token_hash,
            expires_at=expires_at, ip_address=ip, user_agent=user_agent,
            active_organization_id=active_organization_id,
        )
        self.session.add(rec)
        await self.session.flush()
        return rec

    async def update_active_org(self, token_id: uuid.UUID, organization_id: uuid.UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(active_organization_id=organization_id)
        )

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def mark_rotated(self, token_id: uuid.UUID, replaced_by: uuid.UUID) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(rotated_at=_now(), revoked_at=_now(), revoked_reason="rotated", replaced_by=replaced_by)
        )

    async def revoke_family(self, family_id: uuid.UUID, reason: str) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=_now(), revoked_reason=reason)
        )

    async def revoke_all_for_user(self, user_id: uuid.UUID, reason: str) -> None:
        await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=_now(), revoked_reason=reason)
        )


class AuthTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, *, user_id: uuid.UUID, purpose: str, token_hash: str, expires_at: datetime
    ) -> AuthToken:
        rec = AuthToken(
            user_id=user_id, purpose=purpose, token_hash=token_hash, expires_at=expires_at
        )
        self.session.add(rec)
        await self.session.flush()
        return rec

    async def get_active_by_hash(self, token_hash: str, purpose: str) -> AuthToken | None:
        stmt = select(AuthToken).where(
            AuthToken.token_hash == token_hash,
            AuthToken.purpose == purpose,
            AuthToken.consumed_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def consume(self, token_id: uuid.UUID) -> None:
        await self.session.execute(
            update(AuthToken).where(AuthToken.id == token_id).values(consumed_at=_now())
        )
