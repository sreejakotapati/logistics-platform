"""Users & Organizations router.

Tenant-plane routes use `get_tenant_session` (RLS + membership guard); identity-plane routes
(create another org, list my orgs, invitation preview/accept, profile) use the auth identity session.
No RBAC enforcement — that is S2-T5.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_system_session
from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.organizations.schemas import (
    InvitationCreate,
    InvitationPreview,
    InvitationSummary,
    MemberSummary,
    MemberUpdate,
    MessageResponse,
    OrganizationCreate,
    OrganizationProfile,
    OrganizationProfileUpdate,
    OrganizationSettings,
    OrganizationSettingsUpdate,
    OrganizationSummary,
    UserProfile,
    UserProfileUpdate,
)
from app.modules.organizations.service import (
    AccountService,
    InvitationService,
    MembershipService,
    OrganizationService,
)
from app.modules.tenancy.context import TenantContext
from app.modules.rbac.deps import require_permission
from app.modules.tenancy.deps import get_tenant_context, get_tenant_session

router = APIRouter(tags=["organizations"])


def _profile(org) -> OrganizationProfile:
    return OrganizationProfile(
        id=org.id, name=org.name, slug=org.slug, status=org.status, legal_name=org.legal_name,
        gstin=org.gstin, country_code=org.country_code, currency=org.currency,
        contact_email=org.contact_email, contact_phone=org.contact_phone, website=org.website,
        address_line1=org.address_line1, address_line2=org.address_line2, city=org.city,
        state=org.state, postal_code=org.postal_code,
    )


# ===================================================== organization (tenant)
@router.get("/organizations/current", response_model=OrganizationProfile, dependencies=[Depends(require_permission("org:read"))])
async def get_current_organization(
    session: AsyncSession = Depends(get_tenant_session),
) -> OrganizationProfile:
    return _profile(await OrganizationService(session).get_current())


@router.patch("/organizations/current", response_model=OrganizationProfile, dependencies=[Depends(require_permission("org:update"))])
async def update_current_organization(
    body: OrganizationProfileUpdate, session: AsyncSession = Depends(get_tenant_session),
) -> OrganizationProfile:
    org = await OrganizationService(session).update_profile(body.model_dump(exclude_unset=True))
    return _profile(org)


@router.get("/organizations/current/settings", response_model=OrganizationSettings, dependencies=[Depends(require_permission("org:read"))])
async def get_settings_endpoint(
    session: AsyncSession = Depends(get_tenant_session),
) -> OrganizationSettings:
    org = await OrganizationService(session).get_current()
    return OrganizationSettings(settings=org.settings or {})


@router.patch("/organizations/current/settings", response_model=OrganizationSettings, dependencies=[Depends(require_permission("org:update"))])
async def update_settings_endpoint(
    body: OrganizationSettingsUpdate, session: AsyncSession = Depends(get_tenant_session),
) -> OrganizationSettings:
    org = await OrganizationService(session).update_settings(body.settings)
    return OrganizationSettings(settings=org.settings or {})


@router.post("/organizations/current/close", response_model=MessageResponse, dependencies=[Depends(require_permission("org:update"))])
async def close_organization(
    session: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    await OrganizationService(session).close()
    return MessageResponse(message="Organization closed")


# =========================================================== members (tenant)
@router.get("/organizations/current/members", response_model=list[MemberSummary], dependencies=[Depends(require_permission("users:read"))])
async def list_members(session: AsyncSession = Depends(get_tenant_session)) -> list[MemberSummary]:
    rows = await MembershipService(session).list_members()
    return [
        MemberSummary(
            user_id=u.id, email=u.email, full_name=u.full_name,
            membership_status=m.status, is_primary=m.is_primary,
        )
        for m, u in rows
    ]


@router.get("/organizations/current/members/{user_id}", response_model=MemberSummary, dependencies=[Depends(require_permission("users:read"))])
async def get_member(
    user_id: uuid.UUID, session: AsyncSession = Depends(get_tenant_session),
) -> MemberSummary:
    m, u = await MembershipService(session).get_member(user_id)
    return MemberSummary(
        user_id=u.id, email=u.email, full_name=u.full_name,
        membership_status=m.status, is_primary=m.is_primary,
    )


@router.patch("/organizations/current/members/{user_id}", response_model=MessageResponse, dependencies=[Depends(require_permission("users:update"))])
async def update_member(
    user_id: uuid.UUID, body: MemberUpdate, session: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    await MembershipService(session).update_member_status(user_id, body.status)
    return MessageResponse(message="Member updated")


@router.delete("/organizations/current/members/{user_id}", response_model=MessageResponse, dependencies=[Depends(require_permission("users:remove"))])
async def remove_member(
    user_id: uuid.UUID, ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    await MembershipService(session).remove_member(user_id, ctx.user_id)
    return MessageResponse(message="Member removed")


@router.post("/organizations/current/leave", response_model=MessageResponse)
async def leave_organization(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_tenant_session),
) -> MessageResponse:
    await MembershipService(session).leave(ctx.user_id)
    return MessageResponse(message="You have left the organization")


# ======================================================= invitations (tenant)
@router.post("/organizations/current/invitations", response_model=InvitationSummary,
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("users:invite"))])
async def create_invitation(
    body: InvitationCreate, ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_tenant_session), settings: Settings = Depends(get_settings),
) -> InvitationSummary:
    inv, _raw = await InvitationService(session, settings).create(
        ctx.organization_id, ctx.user_id, body.email, body.role_id
    )
    return InvitationSummary(
        id=inv.id, email=inv.email, status=inv.status, role_id=inv.role_id,
        expires_at=inv.expires_at.isoformat(),
    )


@router.get("/organizations/current/invitations", response_model=list[InvitationSummary], dependencies=[Depends(require_permission("users:read"))])
async def list_invitations(
    session: AsyncSession = Depends(get_tenant_session), settings: Settings = Depends(get_settings),
) -> list[InvitationSummary]:
    invs = await InvitationService(session, settings).list_pending()
    return [
        InvitationSummary(
            id=i.id, email=i.email, status=i.status, role_id=i.role_id,
            expires_at=i.expires_at.isoformat(),
        )
        for i in invs
    ]


@router.delete("/organizations/current/invitations/{invitation_id}", response_model=MessageResponse, dependencies=[Depends(require_permission("users:invite"))])
async def revoke_invitation(
    invitation_id: uuid.UUID, session: AsyncSession = Depends(get_tenant_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await InvitationService(session, settings).revoke(invitation_id)
    return MessageResponse(message="Invitation revoked")


# ================================================= account / join (identity)
@router.post("/organizations", response_model=OrganizationProfile, status_code=status.HTTP_201_CREATED)
async def create_organization(
    body: OrganizationCreate, current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session),
) -> OrganizationProfile:
    org = await AccountService(session).create_organization(current.id, body.name, body.slug)
    await session.commit()
    return _profile(org)


@router.get("/organizations", response_model=list[OrganizationSummary])
async def list_my_organizations(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session),
) -> list[OrganizationSummary]:
    rows = await AccountService(session).list_my_organizations(current.id)
    return [
        OrganizationSummary(
            id=o.id, name=o.name, slug=o.slug, status=o.status,
            is_primary=m.is_primary, membership_status=m.status,
        )
        for m, o in rows
    ]


@router.get("/invitations/{token}", response_model=InvitationPreview)
async def preview_invitation(
    token: str, session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> InvitationPreview:
    inv, org, expired = await InvitationService(session, settings).preview(token)
    return InvitationPreview(
        organization_id=org.id, organization_name=org.name, email=inv.email,
        status=inv.status, expired=expired,
    )


@router.post("/invitations/{token}/accept", response_model=MessageResponse)
async def accept_invitation(
    token: str, current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session), settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await InvitationService(session, settings).accept(token, current.id, current.email)
    await session.commit()
    return MessageResponse(message="Invitation accepted; membership created")


# ===================================================== user profile (identity)
@router.get("/users/me", response_model=UserProfile)
async def get_my_profile(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session),
) -> UserProfile:
    user = await AccountService(session).get_profile(current.id)
    return UserProfile(
        id=user.id, email=user.email, full_name=user.full_name, status=user.status,
        email_verified=user.email_verified_at is not None,
    )


@router.patch("/users/me", response_model=UserProfile)
async def update_my_profile(
    body: UserProfileUpdate, current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session),
) -> UserProfile:
    user = await AccountService(session).update_profile(current.id, body.full_name)
    await session.commit()
    return UserProfile(
        id=user.id, email=user.email, full_name=user.full_name, status=user.status,
        email_verified=user.email_verified_at is not None,
    )
