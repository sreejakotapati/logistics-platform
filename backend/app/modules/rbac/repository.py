"""RBAC repository layer — pure data access (no caching, no authz decisions)."""
from __future__ import annotations

import uuid

from sqlalchemy import or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Role, UserOrganization, UserOrganizationRole
from app.modules.rbac.models import Permission, PlatformAdmin, RolePermission


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self) -> list[Permission]:
        stmt = select(Permission).where(Permission.deleted_at.is_(None)).order_by(Permission.key)
        return list((await self.session.execute(stmt)).scalars().all())

    async def all_keys(self) -> set[str]:
        stmt = select(Permission.key).where(Permission.deleted_at.is_(None))
        return set((await self.session.execute(stmt)).scalars().all())


class ResolutionRepository:
    """Effective-permission resolution: union over a user's roles → role_permissions → permissions."""

    _SQL = text(
        """
        SELECT DISTINCT p.key
        FROM user_organizations uo
        JOIN user_organization_roles uor
            ON uor.user_organization_id = uo.id AND uor.deleted_at IS NULL
        JOIN roles r ON r.id = uor.role_id AND r.deleted_at IS NULL
        JOIN role_permissions rp ON rp.role_id = r.id AND rp.deleted_at IS NULL
        JOIN permissions p ON p.id = rp.permission_id AND p.deleted_at IS NULL
        WHERE uo.user_id = :uid AND uo.organization_id = :oid
          AND uo.status = 'active' AND uo.deleted_at IS NULL
        """
    )

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def permission_keys(self, user_id: uuid.UUID, organization_id: uuid.UUID) -> set[str]:
        rows = await self.session.execute(self._SQL, {"uid": str(user_id), "oid": str(organization_id)})
        return {r[0] for r in rows.all()}


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_org(self, organization_id: uuid.UUID) -> list[Role]:
        stmt = (
            select(Role)
            .where(
                Role.deleted_at.is_(None),
                or_(Role.organization_id.is_(None), Role.organization_id == organization_id),
            )
            .order_by(Role.is_system.desc(), Role.name)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get(self, role_id: uuid.UUID) -> Role | None:
        stmt = select(Role).where(Role.id == role_id, Role.deleted_at.is_(None))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create_custom(
        self, *, organization_id: uuid.UUID, name: str, description: str | None
    ) -> Role:
        role = Role(organization_id=organization_id, name=name, description=description, is_system=False)
        self.session.add(role)
        await self.session.flush()
        return role

    async def add_permissions(
        self, *, role_id: uuid.UUID, organization_id: uuid.UUID, permission_ids: list[uuid.UUID]
    ) -> None:
        for pid in permission_ids:
            self.session.add(
                RolePermission(role_id=role_id, permission_id=pid, organization_id=organization_id)
            )
        await self.session.flush()


class AssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def membership_id(self, user_id: uuid.UUID, organization_id: uuid.UUID) -> uuid.UUID | None:
        stmt = select(UserOrganization.id).where(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == organization_id,
            UserOrganization.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_membership(self, membership_id: uuid.UUID) -> list[Role]:
        stmt = (
            select(Role)
            .join(UserOrganizationRole, UserOrganizationRole.role_id == Role.id)
            .where(
                UserOrganizationRole.user_organization_id == membership_id,
                UserOrganizationRole.deleted_at.is_(None),
            )
            .order_by(Role.name)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def exists(self, membership_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        stmt = select(UserOrganizationRole.id).where(
            UserOrganizationRole.user_organization_id == membership_id,
            UserOrganizationRole.role_id == role_id,
            UserOrganizationRole.deleted_at.is_(None),
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def assign(
        self, *, membership_id: uuid.UUID, role_id: uuid.UUID, organization_id: uuid.UUID
    ) -> UserOrganizationRole:
        row = UserOrganizationRole(
            user_organization_id=membership_id, role_id=role_id, organization_id=organization_id
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def remove(self, membership_id: uuid.UUID, role_id: uuid.UUID) -> int:
        result = await self.session.execute(
            update(UserOrganizationRole)
            .where(
                UserOrganizationRole.user_organization_id == membership_id,
                UserOrganizationRole.role_id == role_id,
                UserOrganizationRole.deleted_at.is_(None),
            )
            .values(deleted_at=text("now()"))
        )
        return result.rowcount or 0


class PlatformAdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_admin(self, user_id: uuid.UUID) -> bool:
        stmt = select(PlatformAdmin.id).where(PlatformAdmin.user_id == user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def list(self) -> list[PlatformAdmin]:
        return list((await self.session.execute(select(PlatformAdmin))).scalars().all())

    async def add(self, user_id: uuid.UUID, granted_by: uuid.UUID | None) -> None:
        if not await self.is_admin(user_id):
            self.session.add(PlatformAdmin(user_id=user_id, granted_by=granted_by))
            await self.session.flush()

    async def remove(self, user_id: uuid.UUID) -> None:
        await self.session.execute(
            text("DELETE FROM platform_admins WHERE user_id = :uid"), {"uid": str(user_id)}
        )
