"""Service layer for Users & Organizations — business rules + invitation workflow.

Tenant operations receive the RLS tenant session (org context already set + membership validated by the
guard). Identity operations (create org, list my orgs, invitation preview/accept) receive the privileged
session because they span orgs or act before membership exists. NO RBAC checks here — any authenticated
active member may perform these; permission enforcement is S2-T5.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.modules.auth import tokens
from app.modules.auth.models import Role
from app.modules.organizations.models import Organization, UserOrganization
from app.modules.organizations.repository import (
    InvitationRepository,
    MembershipRepository,
    OrganizationRepository,
    UserProfileRepository,
)

logger = logging.getLogger("app.organizations")

_INVITE_TTL_DAYS = 7


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


# ============================================================ organizations
class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.orgs = OrganizationRepository(session)

    async def get_current(self) -> Organization:
        org = await self.orgs.get_current()
        if org is None:
            raise NotFoundError("Active organization not found")
        return org

    async def update_profile(self, values: dict) -> Organization:
        org = await self.get_current()
        if org.status == "closed":
            raise ConflictError("Organization is closed")
        clean = {k: v for k, v in values.items() if v is not None}
        return await self.orgs.update_profile(org, clean)

    async def update_settings(self, patch: dict) -> Organization:
        org = await self.get_current()
        if org.status == "closed":
            raise ConflictError("Organization is closed")
        return await self.orgs.update_settings(org, patch)

    async def close(self) -> None:
        org = await self.get_current()
        if org.status == "closed":
            raise ConflictError("Organization is already closed")
        await self.orgs.close(org)


# =============================================================== membership
class MembershipService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.members = MembershipRepository(session)

    async def list_members(self):
        return await self.members.list_members()

    async def get_member(self, user_id: uuid.UUID):
        row = await self.members.get_member(user_id)
        if row is None:
            raise NotFoundError("Member not found")
        return row

    async def update_member_status(self, user_id: uuid.UUID, status: str) -> None:
        membership = await self.members.get_membership(user_id)
        if membership is None:
            raise NotFoundError("Member not found")
        await self.members.update_status(membership, status)

    async def remove_member(self, user_id: uuid.UUID, actor_id: uuid.UUID) -> None:
        if user_id == actor_id:
            raise ValidationError("Use the leave endpoint to remove yourself")
        membership = await self.members.get_membership(user_id)
        if membership is None:
            raise NotFoundError("Member not found")
        if await self.members.active_member_count() <= 1:
            raise ConflictError("Cannot remove the last active member of the organization")
        await self.members.soft_remove(membership)

    async def leave(self, user_id: uuid.UUID) -> None:
        membership = await self.members.get_membership(user_id)
        if membership is None:
            raise NotFoundError("You are not a member of this organization")
        if await self.members.active_member_count() <= 1:
            raise ConflictError("The last active member cannot leave; close the organization instead")
        await self.members.soft_remove(membership)


# =============================================================== invitations
class InvitationService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.invites = InvitationRepository(session)
        self.members = MembershipRepository(session)
        self.users = UserProfileRepository(session)

    # ---- tenant-plane (RLS): create / list / revoke ----
    async def create(
        self, organization_id: uuid.UUID, inviter_id: uuid.UUID, email: str, role_id: uuid.UUID | None
    ):
        existing_user = await self.users.get_by_email(email)
        if existing_user and await self.members.exists_active(existing_user.id, organization_id):
            raise ConflictError("That email is already an active member")
        if await self.invites.pending_for_email(organization_id, email):
            raise ConflictError("A pending invitation already exists for that email")
        raw = tokens.generate_url_token()
        inv = await self.invites.create(
            organization_id=organization_id, email=email, role_id=role_id, invited_by=inviter_id,
            token_hash=tokens.hash_token(raw), expires_at=_now() + timedelta(days=_INVITE_TTL_DAYS),
        )
        logger.info("org-invitation link: %s/invitations/%s/accept", self.settings.frontend_base_url, raw)
        return inv, raw

    async def list_pending(self):
        return await self.invites.list_pending()

    async def revoke(self, invitation_id: uuid.UUID) -> None:
        inv = await self.invites.get_by_id(invitation_id)
        if inv is None:
            raise NotFoundError("Invitation not found")
        if inv.status != "pending":
            raise ConflictError("Only pending invitations can be revoked")
        await self.invites.revoke(inv)

    # ---- identity-plane (privileged): preview / accept ----
    async def preview(self, raw_token: str):
        inv = await self.invites.get_by_token_hash(tokens.hash_token(raw_token))
        if inv is None:
            raise NotFoundError("Invitation not found")
        org = (
            await self.session.execute(
                select(Organization).where(Organization.id == inv.organization_id)
            )
        ).scalar_one()
        return inv, org, inv.expires_at <= _now()

    async def accept(self, raw_token: str, user_id: uuid.UUID, user_email: str):
        inv = await self.invites.get_by_token_hash(tokens.hash_token(raw_token))
        if inv is None:
            raise NotFoundError("Invitation not found")
        if inv.status != "pending":
            raise ConflictError("Invitation is not pending")
        if inv.expires_at <= _now():
            raise ValidationError("Invitation has expired")
        if inv.email.lower() != user_email.lower():
            raise ValidationError("This invitation was issued to a different email address")
        if await self.members.exists_active(user_id, inv.organization_id):
            raise ConflictError("You are already a member of this organization")
        has_primary = (
            await self.session.execute(
                select(func.count()).select_from(UserOrganization).where(
                    UserOrganization.user_id == user_id,
                    UserOrganization.is_primary.is_(True),
                    UserOrganization.deleted_at.is_(None),
                )
            )
        ).scalar_one()
        membership = await self.members.create(
            user_id=user_id, organization_id=inv.organization_id,
            is_primary=(has_primary == 0), status="active", invited_by=inv.invited_by,
        )
        if inv.role_id is not None:
            self.session.add(
                _assignment(membership.id, inv.role_id, inv.organization_id)
            )
        await self.invites.mark_accepted(inv, user_id)
        return inv.organization_id


def _assignment(user_organization_id, role_id, organization_id):
    from app.modules.auth.models import UserOrganizationRole

    return UserOrganizationRole(
        user_organization_id=user_organization_id, role_id=role_id, organization_id=organization_id
    )


# ================================================================= account
class AccountService:
    """Cross-org identity actions: create another org, list my orgs, profile."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserProfileRepository(session)
        self.members = MembershipRepository(session)

    async def create_organization(self, user_id: uuid.UUID, name: str, slug: str | None):
        org = Organization(name=name, slug=slug or _slugify(name))
        self.session.add(org)
        await self.session.flush()
        has_primary = (
            await self.session.execute(
                select(func.count()).select_from(UserOrganization).where(
                    UserOrganization.user_id == user_id,
                    UserOrganization.is_primary.is_(True),
                    UserOrganization.deleted_at.is_(None),
                )
            )
        ).scalar_one()
        membership = await self.members.create(
            user_id=user_id, organization_id=org.id, is_primary=(has_primary == 0), status="active",
        )
        role_id = (
            await self.session.execute(
                select(Role.id).where(Role.organization_id.is_(None), func.lower(Role.name) == "org admin")
            )
        ).scalar_one_or_none()
        if role_id is not None:
            self.session.add(_assignment(membership.id, role_id, org.id))
        return org

    async def list_my_organizations(self, user_id: uuid.UUID):
        stmt = (
            select(UserOrganization, Organization)
            .join(Organization, Organization.id == UserOrganization.organization_id)
            .where(UserOrganization.user_id == user_id, UserOrganization.deleted_at.is_(None))
            .order_by(UserOrganization.is_primary.desc(), Organization.name.asc())
        )
        return list((await self.session.execute(stmt)).all())

    async def get_profile(self, user_id: uuid.UUID):
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def update_profile(self, user_id: uuid.UUID, full_name: str):
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        await self.users.update_profile(user, full_name)
        return user
