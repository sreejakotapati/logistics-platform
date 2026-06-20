"""Auth service layer — orchestration over the identity-plane session.

Runs on the BYPASSRLS identity session: registration/provisioning create org+user+membership before any
org context exists, and identity reads (memberships, /me) legitimately span orgs. Tenant business data
(S2-T4+) uses the RLS-enforced session instead.
"""
from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError, ValidationError
from app.core.security import hash_password, needs_rehash, verify_password
from app.modules.auth import tokens
from app.modules.security.audit import write_security_event
from app.modules.security.policy import PasswordPolicy
from app.modules.auth.repository import (
    AuthTokenRepository,
    MembershipRepository,
    OrganizationRepository,
    RefreshTokenRepository,
    RoleRepository,
    UserOrganizationRoleRepository,
    UserRepository,
)

logger = logging.getLogger("app.auth")

_DUMMY_HASH = hash_password("timing-equalization-placeholder")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


@dataclass
class IssuedTokens:
    access_token: str
    expires_in: int
    refresh_raw: str


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)
        self.orgs = OrganizationRepository(session)
        self.memberships = MembershipRepository(session)
        self.roles = RoleRepository(session)
        self.assignments = UserOrganizationRoleRepository(session)
        self.refresh = RefreshTokenRepository(session)
        self.auth_tokens = AuthTokenRepository(session)

    # ----------------------------------------------------------- token issue
    async def _issue(self, user_id: uuid.UUID, org_id: uuid.UUID | None,
                     ip: str | None, ua: str | None) -> IssuedTokens:
        access, expires_in = tokens.issue_access_token(
            self.settings, user_id=str(user_id), org_id=str(org_id) if org_id else None
        )
        raw = tokens.generate_refresh_secret()
        await self.refresh.create(
            user_id=user_id, family_id=uuid.uuid4(), token_hash=tokens.hash_token(raw),
            expires_at=_now() + timedelta(days=self.settings.refresh_token_ttl_days),
            ip=ip, user_agent=ua, active_organization_id=org_id,
        )
        return IssuedTokens(access_token=access, expires_in=expires_in, refresh_raw=raw)

    async def _new_verification_token(self, user_id: uuid.UUID) -> str:
        raw = tokens.generate_url_token()
        await self.auth_tokens.create(
            user_id=user_id, purpose="email_verification", token_hash=tokens.hash_token(raw),
            expires_at=_now() + timedelta(hours=self.settings.email_verification_ttl_hours),
        )
        logger.info("email-verification link: %s/verify-email?token=%s",
                    self.settings.frontend_base_url, raw)
        return raw

    async def _new_reset_token(self, user_id: uuid.UUID) -> str:
        raw = tokens.generate_url_token()
        await self.auth_tokens.create(
            user_id=user_id, purpose="password_reset", token_hash=tokens.hash_token(raw),
            expires_at=_now() + timedelta(minutes=self.settings.password_reset_ttl_minutes),
        )
        logger.info("password-reset link: %s/reset-password?token=%s",
                    self.settings.frontend_base_url, raw)
        return raw

    async def _bootstrap_org(self, *, org_name: str, org_slug: str | None,
                             admin_email: str, admin_full_name: str,
                             admin_password: str | None, admin_status: str):
        if await self.users.get_by_email(admin_email):
            raise ConflictError("A user with this email already exists")
        org = await self.orgs.create(name=org_name, slug=org_slug or _slugify(org_name))
        user = await self.users.create(
            email=admin_email,
            password_hash=hash_password(admin_password) if admin_password else None,
            full_name=admin_full_name, status=admin_status,
        )
        membership = await self.memberships.create(
            user_id=user.id, organization_id=org.id, is_primary=True, status="active",
        )
        role_id = await self.roles.system_role_id("Org Admin")
        if role_id is not None:
            await self.assignments.assign(
                user_organization_id=membership.id, role_id=role_id, organization_id=org.id
            )
        return org, user

    # --------------------------------------------------------------- onboarding
    async def register(self, data, ip: str | None, ua: str | None) -> IssuedTokens:
        """Path A — self-service. Creates org + user + Org Admin membership, then signs in."""
        PasswordPolicy(self.settings).validate(data.password)
        org, user = await self._bootstrap_org(
            org_name=data.organization_name, org_slug=data.organization_slug,
            admin_email=data.email, admin_full_name=data.full_name,
            admin_password=data.password, admin_status="active",
        )
        await self._new_verification_token(user.id)
        issued = await self._issue(user.id, org.id, ip, ua)
        await self.session.commit()
        return issued

    async def provision(self, data) -> tuple[uuid.UUID, uuid.UUID, str]:
        """Path B — Super Admin provisioning. Admin may be created with or without a password."""
        if data.admin_password:
            PasswordPolicy(self.settings).validate(data.admin_password)
        status = "active" if data.admin_password else "invited"
        org, user = await self._bootstrap_org(
            org_name=data.organization_name, org_slug=data.organization_slug,
            admin_email=data.admin_email, admin_full_name=data.admin_full_name,
            admin_password=data.admin_password, admin_status=status,
        )
        if data.admin_password is None:
            await self._new_reset_token(user.id)   # invite: admin sets password via reset link
        await self._new_verification_token(user.id)
        await self.session.commit()
        return org.id, user.id, status

    # -------------------------------------------------------------- session ops
    async def login(self, email: str, password: str, ip: str | None, ua: str | None) -> IssuedTokens:
        user = await self.users.get_by_email(email)
        if user is None or not user.password_hash:
            verify_password(password, _DUMMY_HASH)  # equalize timing
            raise UnauthorizedError("Invalid email or password")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if user.status in ("suspended", "disabled"):
            raise UnauthorizedError("Account is not active")
        if needs_rehash(user.password_hash):
            await self.users.set_password(user.id, hash_password(password))
        primary = await self.memberships.get_primary(user.id)
        issued = await self._issue(user.id, primary.organization_id if primary else None, ip, ua)
        await self.session.commit()
        return issued

    async def refresh_session(self, raw: str, ip: str | None, ua: str | None) -> IssuedTokens:
        rec = await self.refresh.get_by_hash(tokens.hash_token(raw))
        if rec is None:
            raise UnauthorizedError("Invalid refresh token")
        if rec.rotated_at is not None or rec.revoked_at is not None:
            # A consumed/revoked token was presented again -> token theft. Kill the whole family.
            await self.refresh.revoke_family(rec.family_id, reason="reuse_detected")
            await write_security_event(
                self.session, action="security.refresh_reuse_detected", actor_id=rec.user_id,
                entity_type="session", entity_id=rec.family_id,
                metadata={"reason": "reuse_detected"}, ip=ip, user_agent=ua,
            )
            await self.session.commit()
            logger.warning("refresh reuse detected; family %s revoked", rec.family_id)
            raise UnauthorizedError("Refresh token reuse detected")
        if rec.expires_at <= _now():
            raise UnauthorizedError("Refresh token expired")
        # Preserve the session's active org across refreshes (survives org-switch).
        active_org = rec.active_organization_id
        if active_org is None:
            primary = await self.memberships.get_primary(rec.user_id)
            active_org = primary.organization_id if primary else None
        # Rotate within the same family.
        new_raw = tokens.generate_refresh_secret()
        new_rec = await self.refresh.create(
            user_id=rec.user_id, family_id=rec.family_id, token_hash=tokens.hash_token(new_raw),
            expires_at=_now() + timedelta(days=self.settings.refresh_token_ttl_days), ip=ip, user_agent=ua,
            active_organization_id=active_org,
        )
        await self.refresh.mark_rotated(rec.id, replaced_by=new_rec.id)
        access, expires_in = tokens.issue_access_token(
            self.settings, user_id=str(rec.user_id), org_id=str(active_org) if active_org else None,
        )
        await self.session.commit()
        return IssuedTokens(access_token=access, expires_in=expires_in, refresh_raw=new_raw)

    async def switch_active_org(
        self, user_id: uuid.UUID, target_org_id: uuid.UUID, raw_refresh: str | None
    ) -> tuple[str, int, uuid.UUID]:
        """Validate membership in the target org, persist it on the session, mint a NEW access token."""
        membership = await self.memberships.get_active(user_id, target_org_id)
        if membership is None:
            raise ForbiddenError("You are not an active member of the target organization")
        if raw_refresh:
            rec = await self.refresh.get_by_hash(tokens.hash_token(raw_refresh))
            if rec is not None and rec.revoked_at is None:
                await self.refresh.update_active_org(rec.id, target_org_id)
        access, expires_in = tokens.issue_access_token(
            self.settings, user_id=str(user_id), org_id=str(target_org_id)
        )
        await self.session.commit()
        return access, expires_in, target_org_id

    async def logout(self, raw: str | None) -> None:
        if raw:
            rec = await self.refresh.get_by_hash(tokens.hash_token(raw))
            if rec is not None:
                await self.refresh.revoke_family(rec.family_id, reason="logout")
                await write_security_event(
                    self.session, action="security.logout", actor_id=rec.user_id,
                    entity_type="session", entity_id=rec.family_id, metadata={},
                )
                await self.session.commit()

    # ------------------------------------------------------------ reset / verify
    async def request_password_reset(self, email: str) -> None:
        user = await self.users.get_by_email(email)
        if user is not None:
            await self._new_reset_token(user.id)
            await self.session.commit()
        # Always succeed (no account enumeration).

    async def confirm_password_reset(self, raw: str, new_password: str) -> None:
        rec = await self.auth_tokens.get_active_by_hash(tokens.hash_token(raw), "password_reset")
        if rec is None or rec.expires_at <= _now():
            raise ValidationError("Invalid or expired reset token")
        PasswordPolicy(self.settings).validate(new_password)
        await self.users.set_password(rec.user_id, hash_password(new_password))
        await self.auth_tokens.consume(rec.id)
        await self.refresh.revoke_all_for_user(rec.user_id, reason="password_reset")
        await write_security_event(
            self.session, action="security.password_reset", actor_id=rec.user_id,
            entity_type="user", entity_id=rec.user_id, metadata={"sessions_revoked": True},
        )
        await self.session.commit()

    async def verify_email(self, raw: str) -> None:
        rec = await self.auth_tokens.get_active_by_hash(tokens.hash_token(raw), "email_verification")
        if rec is None or rec.expires_at <= _now():
            raise ValidationError("Invalid or expired verification token")
        await self.users.mark_email_verified(rec.user_id)
        await self.auth_tokens.consume(rec.id)
        await self.session.commit()

    async def resend_verification(self, email: str) -> None:
        user = await self.users.get_by_email(email)
        if user is not None and user.email_verified_at is None:
            await self._new_verification_token(user.id)
            await self.session.commit()

    # --------------------------------------------------------------------- me
    async def me(self, user_id: uuid.UUID):
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")
        rows = await self.memberships.list_for_user(user_id)
        primary = next((m for m, _ in rows if m.is_primary), None)
        return user, rows, (primary.organization_id if primary else None)
