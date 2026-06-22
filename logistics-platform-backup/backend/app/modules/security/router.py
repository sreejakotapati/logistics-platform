"""Security endpoints: password policy (public) and the abuse dashboard (platform-admin only).

Session-management endpoints live under /auth (the refresh cookie is scoped there, so the current session
can be identified without widening the cookie's path). All endpoints here are additive.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.core.redis import get_client
from app.modules.rbac.deps import require_platform_permission
from app.modules.security.abuse import AbuseMonitor
from app.modules.security.policy import PasswordPolicy
from app.modules.security.schemas import AbuseSnapshotOut, PasswordPolicyOut

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/policy", response_model=PasswordPolicyOut)
async def password_policy(settings: Settings = Depends(get_settings)) -> PasswordPolicyOut:
    return PasswordPolicyOut(**PasswordPolicy(settings).describe())


@router.get(
    "/abuse", response_model=AbuseSnapshotOut,
    dependencies=[Depends(require_platform_permission("org:provision"))],
)
async def abuse_snapshot(settings: Settings = Depends(get_settings)) -> AbuseSnapshotOut:
    monitor = AbuseMonitor(get_client(), settings)
    return AbuseSnapshotOut(
        flagged_ips=await monitor.snapshot(),
        locked_accounts=await monitor.locked_accounts(),
        thresholds={
            "login_max_failures": settings.login_max_failures,
            "login_lockout_seconds": settings.login_lockout_seconds,
            "rate_limit_global_per_minute": settings.rate_limit_global_per_minute,
            "rate_limit_auth_per_minute": settings.rate_limit_auth_per_minute,
            "abuse_alert_threshold": settings.abuse_alert_threshold,
        },
    )
