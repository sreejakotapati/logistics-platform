"""Redis fixed-window rate limiter.

Fixed-window counters: cheap (one INCR + one EXPIRE), good enough for abuse throttling. Fail-open — if
Redis is unreachable the request is allowed (availability), because the request is still subject to the
underlying auth controls (password verify, token rotation, RLS) which are never bypassed.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import redis.asyncio as aioredis

logger = logging.getLogger("app.security")


@dataclass
class RateResult:
    allowed: bool
    remaining: int
    retry_after: int
    limit: int


class RateLimiter:
    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis = redis

    async def hit(self, scope: str, key: str, *, limit: int, window: int) -> RateResult:
        now = time.time()
        bucket = int(now // window)
        rkey = f"rl:{scope}:{key}:{bucket}"
        try:
            count = await self.redis.incr(rkey)
            if count == 1:
                await self.redis.expire(rkey, window)
            allowed = count <= limit
            remaining = max(0, limit - count)
            retry_after = 0 if allowed else window - int(now % window)
            return RateResult(allowed, remaining, retry_after, limit)
        except Exception as exc:  # noqa: BLE001 — fail-open
            logger.warning("rate limiter unavailable (%s): allowing request", exc)
            return RateResult(True, limit, 0, limit)
