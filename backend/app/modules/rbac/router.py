"""RBAC router: permission catalog, role admin, role assignment/removal, platform-admin management.

Tenant-plane routes use the RLS tenant session for writes (and audit) and `require_permission` for
authorization; platform routes use the identity session and `require_platform_permission`.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_system_session
from app.modules.rbac.deps import (
    get_effective_permissions,
    require_permission,
    require_platform_permission,
)
from app.modules.rbac.service import PlatformAdminService, RoleAdminService
from app.modules.tenancy.context import TenantContext
from app.modules.tenancy.deps import get_tenant_context, get_tenant_session

router = APIRouter(tags=["rbac"])


# ----------------------------------------------------------------- schemas
class PermissionOut(BaseModel):
    id: uuid.UUID
    key: str
    description: str | None


class RoleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_system: bool
    organization_id: uuid.UUID | None


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=300)
    permission_ids: list[uuid.UUID] = Field(default_factory=list)


class AssignRoleRequest(BaseModel):
    role_id: uuid.UUID


class MessageResponse(BaseModel):
    message: str


# ============================================================== catalog
@router.get(
    "/rbac/permissions", response_model=list[PermissionOut],
    dependencies=[Depends(require_permission("roles:read"))],
)
async def list_permissions(
    session: AsyncSession = Depends(get_tenant_session), redis=Depends(get_redis),
) -> list[PermissionOut]:
    perms = await RoleAdminService(session, redis).list_permissions()
    return [PermissionOut(id=p.id, key=p.key, description=p.description) for p in perms]


@router.get("/rbac/me/permissions", response_model=list[str])
async def my_permissions(perms: list[str] = Depends(get_effective_permissions)) -> list[str]:
    return perms


# ================================================================ roles
@router.get(
    "/organizations/current/roles", response_model=list[RoleOut],
    dependencies=[Depends(require_permission("roles:read"))],
)
async def list_roles(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_tenant_session), redis=Depends(get_redis),
) -> list[RoleOut]:
    roles = await RoleAdminService(session, redis).list_roles(ctx.organization_id)
    return [
        RoleOut(id=r.id, name=r.name, description=r.description, is_system=r.is_system,
                organization_id=r.organization_id)
        for r in roles
    ]


@router.post(
    "/organizations/current/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("roles:manage"))],
)
async def create_role(
    body: RoleCreate, ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_tenant_session), redis=Depends(get_redis),
) -> RoleOut:
    role = await RoleAdminService(session, redis).create_role(
        organization_id=ctx.organization_id, actor_id=ctx.user_id, name=body.name,
        description=body.description, permission_ids=body.permission_ids,
    )
    return RoleOut(id=role.id, name=role.name, description=role.description,
                   is_system=role.is_system, organization_id=role.organization_id)


# ================================================== member role assignment
@router.get(
    "/organizations/current/members/{user_id}/roles", response_model=list[RoleOut],
    dependencies=[Depends(require_permission("roles:read"))],
)
async def list_member_roles(
    user_id: uuid.UUID, ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_tenant_session), redis=Depends(get_redis),
) -> list[RoleOut]:
    roles = await RoleAdminService(session, redis).list_member_roles(ctx.organization_id, user_id)
    return [
        RoleOut(id=r.id, name=r.name, description=r.description, is_system=r.is_system,
                organization_id=r.organization_id)
        for r in roles
    ]


@router.post(
    "/organizations/current/members/{user_id}/roles", response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("roles:manage"))],
)
async def assign_role(
    user_id: uuid.UUID, body: AssignRoleRequest, ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_tenant_session), redis=Depends(get_redis),
) -> MessageResponse:
    await RoleAdminService(session, redis).assign_role(
        organization_id=ctx.organization_id, actor_id=ctx.user_id,
        target_user_id=user_id, role_id=body.role_id,
    )
    return MessageResponse(message="Role assigned")


@router.delete(
    "/organizations/current/members/{user_id}/roles/{role_id}", response_model=MessageResponse,
    dependencies=[Depends(require_permission("roles:manage"))],
)
async def remove_role(
    user_id: uuid.UUID, role_id: uuid.UUID, ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_tenant_session), redis=Depends(get_redis),
) -> MessageResponse:
    await RoleAdminService(session, redis).remove_role(
        organization_id=ctx.organization_id, actor_id=ctx.user_id,
        target_user_id=user_id, role_id=role_id,
    )
    return MessageResponse(message="Role removed")


# ======================================================= platform admins
class PlatformAdminOut(BaseModel):
    user_id: uuid.UUID


@router.get(
    "/admin/platform-admins", response_model=list[PlatformAdminOut],
    dependencies=[Depends(require_platform_permission("org:provision"))],
)
async def list_platform_admins(
    session: AsyncSession = Depends(get_system_session), redis=Depends(get_redis),
) -> list[PlatformAdminOut]:
    rows = await PlatformAdminService(session, redis).list()
    return [PlatformAdminOut(user_id=r.user_id) for r in rows]


@router.post(
    "/admin/platform-admins/{user_id}", response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_platform_admin(
    user_id: uuid.UUID,
    actor: uuid.UUID = Depends(require_platform_permission("org:provision")),
    session: AsyncSession = Depends(get_system_session), redis=Depends(get_redis),
) -> MessageResponse:
    await PlatformAdminService(session, redis).grant(actor, user_id)
    await session.commit()
    return MessageResponse(message="Platform admin granted")


@router.delete("/admin/platform-admins/{user_id}", response_model=MessageResponse)
async def revoke_platform_admin(
    user_id: uuid.UUID,
    actor: uuid.UUID = Depends(require_platform_permission("org:provision")),
    session: AsyncSession = Depends(get_system_session), redis=Depends(get_redis),
) -> MessageResponse:
    await PlatformAdminService(session, redis).revoke(actor, user_id)
    await session.commit()
    return MessageResponse(message="Platform admin revoked")
