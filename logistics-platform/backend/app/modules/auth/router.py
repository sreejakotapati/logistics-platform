"""Auth router — endpoints for registration, provisioning, sessions, reset, verification, /me."""
from __future__ import annotations

import ipaddress
import uuid

from fastapi import APIRouter, Depends, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.redis import get_client
from app.db.session import get_system_session
from app.modules.auth import tokens
from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.security.audit import emit_security_event
from app.modules.security.login_guard import LoginGuard
from app.modules.security.service import SessionService
from app.modules.security.schemas import MessageOut, RevokeResultOut, SessionListOut, SessionOut
from app.modules.auth.schemas import (
    EmailVerifyRequest,
    EmailVerifyResendRequest,
    LoginRequest,
    MeResponse,
    MembershipSummary,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequestRequest,
    ProvisionRequest,
    ProvisionResponse,
    RegisterRequest,
    SwitchOrgResponse,
    TokenResponse,
)
from app.modules.auth.service import AuthService, IssuedTokens
from app.modules.rbac.deps import require_platform_permission

router = APIRouter(prefix="/auth", tags=["auth"])


# --------------------------------------------------------------------- helpers
def _service(session: AsyncSession, settings: Settings) -> AuthService:
    return AuthService(session, settings)


def _client(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    try:
        ip = str(ipaddress.ip_address(ip)) if ip else None
    except ValueError:
        ip = None  # non-IP host (test client, malformed proxy header) -> store NULL
    return ip, request.headers.get("user-agent")


def _set_refresh_cookie(response: Response, raw: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw,
        max_age=settings.refresh_token_ttl_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path=settings.cookie_path,
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.cookie_path,
        domain=settings.cookie_domain,
    )


def _token_response(issued: IssuedTokens, response: Response, settings: Settings) -> TokenResponse:
    _set_refresh_cookie(response, issued.refresh_raw, settings)
    return TokenResponse(access_token=issued.access_token, expires_in=issued.expires_in)


async def _require_provisioning_key(
    x_provisioning_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    # Deprecated by S2-T5 (permission-based provisioning). Retained only to avoid an unused-import churn.
    raise ForbiddenError("Provisioning is permission-gated")


# ----------------------------------------------------------------- onboarding
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest, request: Request, response: Response,
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    ip, ua = _client(request)
    issued = await _service(session, settings).register(body, ip, ua)
    return _token_response(issued, response, settings)


@router.post(
    "/provision", response_model=ProvisionResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_permission("org:provision"))],
)
async def provision(
    body: ProvisionRequest,
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> ProvisionResponse:
    org_id, user_id, admin_status = await _service(session, settings).provision(body)
    msg = ("Organization provisioned; admin is active."
           if admin_status == "active"
           else "Organization provisioned; admin invited (password-setup link issued).")
    return ProvisionResponse(
        organization_id=org_id, admin_user_id=user_id, admin_status=admin_status, message=msg
    )


# -------------------------------------------------------------------- sessions
@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest, request: Request, response: Response,
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    ip, ua = _client(request)
    guard = LoginGuard(get_client(), settings)

    # Account lockout: a locked account returns the SAME generic error as a wrong password (no enumeration).
    if await guard.is_locked(body.email):
        await emit_security_event(
            settings, action="security.login_blocked",
            metadata={"email": body.email, "reason": "locked"}, ip=ip, user_agent=ua,
        )
        raise UnauthorizedError("Invalid email or password")

    try:
        issued = await _service(session, settings).login(body.email, body.password, ip, ua)
    except UnauthorizedError:
        state = await guard.record_failure(body.email, ip)
        await emit_security_event(
            settings, action="security.login_failed",
            metadata={"email": body.email, "failures": state.failures,
                      "ip_failures": state.ip_failures, "locked": state.locked},
            ip=ip, user_agent=ua,
        )
        raise

    await guard.clear(body.email)

    # Resolve the user id from the freshly minted access token, enforce the concurrent-session cap,
    # and record the successful sign-in.
    uid = None
    try:
        sub = tokens.decode_access_token(settings, issued.access_token).get("sub")
        uid = uuid.UUID(sub) if sub else None
    except Exception:  # noqa: BLE001
        uid = None
    if uid is not None:
        evicted = await SessionService(session, settings).enforce_max_concurrent(uid)
        if evicted:
            await session.commit()
        await emit_security_event(
            settings, action="security.login_succeeded", actor_id=uid,
            metadata={"sessions_evicted": evicted}, ip=ip, user_agent=ua,
        )
    return _token_response(issued, response, settings)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request, response: Response,
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    raw = request.cookies.get(settings.refresh_cookie_name)
    if not raw:
        raise UnauthorizedError("Missing refresh token")
    issued = await _service(session, settings).refresh_session(raw, *_client(request))
    return _token_response(issued, response, settings)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request, response: Response,
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    raw = request.cookies.get(settings.refresh_cookie_name)
    await _service(session, settings).logout(raw)
    _clear_refresh_cookie(response, settings)
    return MessageResponse(message="Logged out")


@router.post("/organizations/{organization_id}/activate", response_model=SwitchOrgResponse)
async def switch_organization(
    organization_id: uuid.UUID,            # target comes from the PATH (never body/header/query)
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> SwitchOrgResponse:
    raw = request.cookies.get(settings.refresh_cookie_name)
    access, expires_in, active = await _service(session, settings).switch_active_org(
        current.id, organization_id, raw
    )
    return SwitchOrgResponse(
        access_token=access, expires_in=expires_in, active_organization_id=active
    )


# ----------------------------------------------------------- reset / verify
@router.post(
    "/password-reset/request", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED
)
async def password_reset_request(
    body: PasswordResetRequestRequest,
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await _service(session, settings).request_password_reset(body.email)
    return MessageResponse(message="If the account exists, a reset link has been sent")


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def password_reset_confirm(
    body: PasswordResetConfirmRequest, response: Response,
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await _service(session, settings).confirm_password_reset(body.token, body.new_password)
    _clear_refresh_cookie(response, settings)  # all sessions revoked; force re-login
    return MessageResponse(message="Password updated")


@router.post("/email/verify", response_model=MessageResponse)
async def email_verify(
    body: EmailVerifyRequest,
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await _service(session, settings).verify_email(body.token)
    return MessageResponse(message="Email verified")


@router.post(
    "/email/verify/resend", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED
)
async def email_verify_resend(
    body: EmailVerifyResendRequest,
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    await _service(session, settings).resend_verification(body.email)
    return MessageResponse(message="If the account exists and is unverified, a link has been sent")


# --------------------------------------------------------------------- me
@router.get("/me", response_model=MeResponse)
async def me(
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> MeResponse:
    user, rows, active_org = await _service(session, settings).me(current.id)
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        email_verified=user.email_verified_at is not None,
        active_organization_id=active_org,
        organizations=[
            MembershipSummary(
                organization_id=org.id, name=org.name, slug=org.slug,
                status=m.status, is_primary=m.is_primary,
            )
            for m, org in rows
        ],
    )


# --------------------------------------------------------------- sessions (S2-T8)
async def _current_family(request: Request, session: AsyncSession, settings: Settings):
    raw = request.cookies.get(settings.refresh_cookie_name)
    if not raw:
        return None
    rec = await _service(session, settings).refresh.get_by_hash(tokens.hash_token(raw))
    return rec.family_id if rec else None


@router.get("/sessions", response_model=SessionListOut)
async def list_sessions(
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> SessionListOut:
    fam = await _current_family(request, session, settings)
    views = await SessionService(session, settings).list_sessions(current.id, fam)
    return SessionListOut(sessions=[SessionOut(**v.__dict__) for v in views])


@router.delete("/sessions/{family_id}", response_model=MessageOut)
async def revoke_session(
    family_id: uuid.UUID, request: Request,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> MessageOut:
    ip, _ = _client(request)
    await SessionService(session, settings).revoke_session(current.id, family_id, ip=ip)
    return MessageOut(message="Session revoked")


@router.post("/sessions/revoke-others", response_model=RevokeResultOut)
async def revoke_other_sessions(
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> RevokeResultOut:
    ip, _ = _client(request)
    fam = await _current_family(request, session, settings)
    revoked = await SessionService(session, settings).revoke_other_sessions(current.id, fam, ip=ip)
    return RevokeResultOut(revoked=revoked)
