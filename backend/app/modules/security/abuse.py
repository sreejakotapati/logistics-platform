"""API-abuse monitoring (Redis).

Tracks rate-limit blocks per client IP and flags IPs that cross the alert threshold. The flagged set is a
sorted set keyed by last-seen timestamp so the snapshot can prune stale entries. Read by the platform
security dashboard endpoint. Fail-open and side-effect-free on the request path.
"""
from __future__ import annotations

import logging
import time

import redis.asyncio as aioredis

from app.core.config import Settings

logger = logging.getLogger("app.security")

_FLAGGED = "sec:flagged_ips"


class AbuseMonitor:
    def __init__(self, redis: aioredis.Redis, settings: Settings) -> None:
        self.redis = redis
        self.s = settings

    async def record_block(self, ip: str) -> int:
        """Count a rate-limit block for this IP within the window; return the running count."""
        try:
            key = f"sec:blocks:{ip}"
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, self.s.rate_limit_window_seconds)
            return int(count)
        except Exception:  # noqa: BLE001
            return 0

    async def flag(self, ip: str) -> None:
        try:
            await self.redis.zadd(_FLAGGED, {ip: time.time()})
        except Exception as exc:  # noqa: BLE001
            logger.warning("abuse flag unavailable (%s)", exc)

    async def is_flagged(self, ip: str) -> bool:
        try:
            return (await self.redis.zscore(_FLAGGED, ip)) is not None
        except Exception:  # noqa: BLE001
            return False

    async def snapshot(self, limit: int = 100) -> list[dict]:
        """Recently-flagged IPs, newest first, pruning entries older than the failure window."""
        try:
            cutoff = time.time() - self.s.login_failure_window_seconds
            await self.redis.zremrangebyscore(_FLAGGED, 0, cutoff)
            rows = await self.redis.zrevrange(_FLAGGED, 0, limit - 1, withscores=True)
            return [{"ip": ip, "last_seen_epoch": int(score)} for ip, score in rows]
        except Exception as exc:  # noqa: BLE001
            logger.warning("abuse snapshot unavailable (%s)", exc)
            return []

    async def locked_accounts(self, limit: int = 100) -> int:
        """Count of currently locked accounts (lock keys). Best-effort via SCAN."""
        try:
            count = 0
            async for _ in self.redis.scan_iter(match="sec:lock:*", count=200):
                count += 1
                if count >= limit:
                    break
            return count
        except Exception:  # noqa: BLE001
            return 0
