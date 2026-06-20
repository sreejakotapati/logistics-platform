"""Auth dependencies. Validates the access token and loads the current user.

This is authentication only — it resolves *who* the caller is and their active org claim. It performs
NO permission checks (RBAC authorization lands in S2-T5).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.db.session import get_system_session
from app.modules.auth import tokens
from app.modules.auth.repository import UserRepository


@dataclass
class CurrentUser:
    id: uuid.UUID
    email: str
    active_org_id: uuid.UUID | None


async def get_current_user(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_system_session),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing bearer token")
    raw = authorization.split(" ", 1)[1].strip()
    try:
        claims = tokens.decode_access_token(settings, raw)
    except Exception as exc:  # noqa: BLE001  (signature/expiry errors -> 401)
        raise UnauthorizedError("Invalid or expired token") from exc
    if claims.get("type") != "access":
        raise UnauthorizedError("Wrong token type")
    sub = claims.get("sub")
    if not sub:
        raise UnauthorizedError("Invalid token")
    user = await UserRepository(session).get_by_id(uuid.UUID(sub))
    if user is None:
        raise UnauthorizedError("User not found")
    org = claims.get("org")
    return CurrentUser(
        id=user.id, email=user.email, active_org_id=uuid.UUID(org) if org else None
    )
