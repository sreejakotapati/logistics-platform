"""RBAC permission cache (Redis).

Effective permissions are cached per (user, scope) where scope is an org id or 'platform'. Every method
is best-effort: if Redis is unavailable the cache silently misses and authorization falls back to the
database — security is never weakened by a cache failure, only performance.
"""
from __future__ import annotations

import json
import logging

logger = logging.getLogger("app.rbac")


def _key(user_id: str, scope: str) -> str:
    return f"rbac:perms:{user_id}:{scope}"


async def get_perms(redis, user_id: str, scope: str) -> set[str] | None:
    try:
        raw = await redis.get(_key(user_id, scope))
        return set(json.loads(raw)) if raw is not None else None
    except Exception as exc:  # noqa: BLE001
        logger.debug("rbac cache get miss (%s)", exc)
        return None


async def set_perms(redis, user_id: str, scope: str, perms: set[str], ttl: int) -> None:
    try:
        await redis.set(_key(user_id, scope), json.dumps(sorted(perms)), ex=ttl)
    except Exception as exc:  # noqa: BLE001
        logger.debug("rbac cache set skipped (%s)", exc)


async def invalidate(redis, user_id: str, scope: str) -> None:
    try:
        await redis.delete(_key(user_id, scope))
    except Exception as exc:  # noqa: BLE001
        logger.debug("rbac cache invalidate skipped (%s)", exc)


async def invalidate_user(redis, user_id: str) -> None:
    """Drop every cached scope for a user (used when platform-admin status changes)."""
    try:
        async for key in redis.scan_iter(match=f"rbac:perms:{user_id}:*"):
            await redis.delete(key)
    except Exception as exc:  # noqa: BLE001
        logger.debug("rbac cache invalidate_user skipped (%s)", exc)
