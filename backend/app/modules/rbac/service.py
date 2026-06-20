"""RBAC services: effective-permission resolution (with Redis cache), role administration, and
platform-admin management. All role-assignment changes are written to the audit log.
"""
from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.modules.rbac import cache
from app.modules.rbac.repository import (
    AssignmentRepository,
    PermissionRepository,
    PlatformAdminRepository,
    ResolutionRepository,
    RoleRepository,
)

logger = logging.getLogger("app.rbac")

PLATFORM_SCOPE = "platform"


async def write_audit(
    session: AsyncSession, *, organization_id: uuid.UUID | None, actor_id: uuid.UUID | None,
    action: str, entity_type: str, entity_id: uuid.UUID | None, metadata: dict,
) -> None:
    await session.execute(
        text(
            "INSERT INTO audit_logs (organization_id, actor_user_id, action, entity_type, entity_id, metadata) "
            "VALUES (:org, :actor, :action, :etype, :eid, CAST(:meta AS jsonb))"
        ),
        {
            "org": str(organization_id) if organization_id else None,
            "actor": str(actor_id) if actor_id else None,
            "action": action, "etype": entity_type,
            "eid": str(entity_id) if entity_id else None, "meta": json.dumps(metadata),
        },
    )


# ===================================================== resolution + cache
class RBACService:
    def __init__(self, session: AsyncSession, redis, settings: Settings) -> None:
        self.session = session
        self.redis = redis
        self.settings = settings
        self.perms = PermissionRepository(session)
        self.resolution = ResolutionRepository(session)
        self.platform = PlatformAdminRepository(session)

    async def effective_permissions(self, user_id: str, organization_id: str) -> set[str]:
        cached = await cache.get_perms(self.redis, user_id, organization_id)
        if cached is not None:
            return cached
        if await self.platform.is_admin(uuid.UUID(user_id)):
            perms = await self.perms.all_keys()                 # Super Admin → full catalog
        else:
            perms = await self.resolution.permission_keys(uuid.UUID(user_id), uuid.UUID(organization_id))
        await cache.set_perms(self.redis, user_id, organization_id, perms, self.settings.rbac_cache_ttl_seconds)
        return perms

    async def platform_permissions(self, user_id: str) -> set[str]:
        cached = await cache.get_perms(self.redis, user_id, PLATFORM_SCOPE)
        if cached is not None:
            return cached
        perms = await self.perms.all_keys() if await self.platform.is_admin(uuid.UUID(user_id)) else set()
        await cache.set_perms(self.redis, user_id, PLATFORM_SCOPE, perms, self.settings.rbac_cache_ttl_seconds)
        return perms


# ============================================================ role admin
class RoleAdminService:
    """Runs on the TENANT session (RLS + org context). Audits every assignment change."""

    def __init__(self, session: AsyncSession, redis) -> None:
        self.session = session
        self.redis = redis
        self.roles = RoleRepository(session)
        self.assignments = AssignmentRepository(session)
        self.perms = PermissionRepository(session)

    async def list_permissions(self):
        return await self.perms.list()

    async def list_roles(self, organization_id: uuid.UUID):
        return await self.roles.list_for_org(organization_id)

    async def create_role(
        self, *, organization_id: uuid.UUID, actor_id: uuid.UUID, name: str,
        description: str | None, permission_ids: list[uuid.UUID],
    ):
        role = await self.roles.create_custom(
            organization_id=organization_id, name=name, description=description
        )
        if permission_ids:
            await self.roles.add_permissions(
                role_id=role.id, organization_id=organization_id, permission_ids=permission_ids
            )
        await write_audit(
            self.session, organization_id=organization_id, actor_id=actor_id, action="role.created",
            entity_type="role", entity_id=role.id,
            metadata={"name": name, "permission_ids": [str(p) for p in permission_ids]},
        )
        return role

    async def list_member_roles(self, organization_id: uuid.UUID, target_user_id: uuid.UUID):
        membership_id = await self.assignments.membership_id(target_user_id, organization_id)
        if membership_id is None:
            raise NotFoundError("Member not found")
        return await self.assignments.list_for_membership(membership_id)

    async def assign_role(
        self, *, organization_id: uuid.UUID, actor_id: uuid.UUID,
        target_user_id: uuid.UUID, role_id: uuid.UUID,
    ) -> None:
        role = await self.roles.get(role_id)
        if role is None:
            raise NotFoundError("Role not found")
        if role.organization_id is not None and role.organization_id != organization_id:
            raise ValidationError("Role does not belong to this organization")
        membership_id = await self.assignments.membership_id(target_user_id, organization_id)
        if membership_id is None:
            raise NotFoundError("Member not found")
        if await self.assignments.exists(membership_id, role_id):
            raise ConflictError("Member already has this role")
        await self.assignments.assign(
            membership_id=membership_id, role_id=role_id, organization_id=organization_id
        )
        await write_audit(
            self.session, organization_id=organization_id, actor_id=actor_id, action="role.assigned",
            entity_type="user_organization_role", entity_id=membership_id,
            metadata={"target_user_id": str(target_user_id), "role_id": str(role_id)},
        )
        await cache.invalidate(self.redis, str(target_user_id), str(organization_id))

    async def remove_role(
        self, *, organization_id: uuid.UUID, actor_id: uuid.UUID,
        target_user_id: uuid.UUID, role_id: uuid.UUID,
    ) -> None:
        membership_id = await self.assignments.membership_id(target_user_id, organization_id)
        if membership_id is None:
            raise NotFoundError("Member not found")
        removed = await self.assignments.remove(membership_id, role_id)
        if not removed:
            raise NotFoundError("Role assignment not found")
        await write_audit(
            self.session, organization_id=organization_id, actor_id=actor_id, action="role.removed",
            entity_type="user_organization_role", entity_id=membership_id,
            metadata={"target_user_id": str(target_user_id), "role_id": str(role_id)},
        )
        await cache.invalidate(self.redis, str(target_user_id), str(organization_id))


# ======================================================== platform admin
class PlatformAdminService:
    """Runs on the identity (BYPASSRLS) session. Platform events audit with organization_id NULL."""

    def __init__(self, session: AsyncSession, redis) -> None:
        self.session = session
        self.redis = redis
        self.repo = PlatformAdminRepository(session)

    async def list(self):
        return await self.repo.list()

    async def grant(self, actor_id: uuid.UUID | None, user_id: uuid.UUID) -> None:
        await self.repo.add(user_id, actor_id)
        await write_audit(
            self.session, organization_id=None, actor_id=actor_id, action="platform_admin.granted",
            entity_type="platform_admin", entity_id=user_id, metadata={"user_id": str(user_id)},
        )
        if self.redis is not None:
            await cache.invalidate_user(self.redis, str(user_id))

    async def revoke(self, actor_id: uuid.UUID | None, user_id: uuid.UUID) -> None:
        if not await self.repo.is_admin(user_id):
            raise NotFoundError("User is not a platform admin")
        await self.repo.remove(user_id)
        await write_audit(
            self.session, organization_id=None, actor_id=actor_id, action="platform_admin.revoked",
            entity_type="platform_admin", entity_id=user_id, metadata={"user_id": str(user_id)},
        )
        if self.redis is not None:
            await cache.invalidate_user(self.redis, str(user_id))

    async def ensure_by_email(self, email: str) -> bool:
        """Idempotent bootstrap: promote a known user to platform admin. Returns True if promoted."""
        row = (
            await self.session.execute(
                text("SELECT id FROM users WHERE lower(email) = lower(:e) AND deleted_at IS NULL"),
                {"e": email},
            )
        ).first()
        if not row:
            return False
        user_id = row[0]
        if await self.repo.is_admin(user_id):
            return False
        await self.repo.add(user_id, None)
        await write_audit(
            self.session, organization_id=None, actor_id=None, action="platform_admin.bootstrapped",
            entity_type="platform_admin", entity_id=user_id, metadata={"email": email},
        )
        return True
