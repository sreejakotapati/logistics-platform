"""Security-event auditing — every security control writes through here.

Security events are platform-scope (organization_id NULL): they surface in the platform audit feed,
never a tenant feed. Two entry points:
  * write_security_event(session, ...)  — reuse the caller's identity session (login/refresh flows).
  * emit_security_event(settings, ...)  — open a short-lived system session (middleware, background).
Both are best-effort for the background path: a failed audit write must never break the request.
"""
from __future__ import annotations

import ipaddress
import json
import logging
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings

logger = logging.getLogger("app.security")

_INSERT = text(
    "INSERT INTO audit_logs (organization_id, actor_user_id, action, entity_type, entity_id, "
    "metadata, ip_address, user_agent) "
    "VALUES (:org, :actor, :action, :etype, :eid, CAST(:meta AS jsonb), CAST(:ip AS inet), :ua)"
)


def _safe_ip(ip: str | None) -> str | None:
    """audit_logs.ip_address is INET — coerce non-IP hosts (e.g. 'testclient', proxy junk) to NULL."""
    if not ip:
        return None
    try:
        return str(ipaddress.ip_address(ip))
    except ValueError:
        return None


def _params(action, actor_id, organization_id, entity_type, entity_id, metadata, ip, ua) -> dict:
    return {
        "org": str(organization_id) if organization_id else None,
        "actor": str(actor_id) if actor_id else None,
        "action": action,
        "etype": entity_type,
        "eid": str(entity_id) if entity_id else None,
        "meta": json.dumps(metadata or {}),
        "ip": _safe_ip(ip),
        "ua": ua,
    }


async def write_security_event(
    session: AsyncSession, *, action: str, actor_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None, entity_type: str = "security",
    entity_id: uuid.UUID | None = None, metadata: dict | None = None,
    ip: str | None = None, user_agent: str | None = None,
) -> None:
    await session.execute(_INSERT, _params(action, actor_id, organization_id, entity_type,
                                           entity_id, metadata, ip, user_agent))


async def emit_security_event(
    settings: Settings, *, action: str, actor_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None, entity_type: str = "security",
    entity_id: uuid.UUID | None = None, metadata: dict | None = None,
    ip: str | None = None, user_agent: str | None = None,
) -> None:
    """Open a dedicated system session and write the event. Never raises."""
    try:
        from app.db import session as db_module

        async with db_module.get_system_sessionmaker()() as s:
            await write_security_event(
                s, action=action, actor_id=actor_id, organization_id=organization_id,
                entity_type=entity_type, entity_id=entity_id, metadata=metadata, ip=ip, user_agent=user_agent,
            )
            await s.commit()
    except Exception as exc:  # noqa: BLE001 — auditing must never break the request path
        logger.warning("security audit write failed for %s: %s", action, exc)
