"""Account lockout + login-abuse tracking (Redis).

Per-account failure counter trips a temporary lock; a separate per-IP failure counter feeds distributed
brute-force detection. Lockout is enforced WITHOUT revealing account existence: a locked login returns the
same generic "invalid credentials" as a wrong password, preserving the codebase's no-enumeration posture.
Fail-open: if Redis is down, lockout is simply not applied — the password check still gates every login.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import redis.asyncio as aioredis

from app.core.config import Settings

logger = logging.getLogger("app.security")


@dataclass
class LockState:
    locked: bool
    failures: int
    ip_failures: int
    lock_seconds: int


def _norm(email: str) -> str:
    return email.strip().lower()


class LoginGuard:
    def __init__(self, redis: aioredis.Redis, settings: Settings) -> None:
        self.redis = redis
        self.s = settings

    def _lock_key(self, email: str) -> str: return f"sec:lock:{_norm(email)}"
    def _fail_key(self, email: str) -> str: return f"sec:fail:{_norm(email)}"
    def _ipfail_key(self, ip: str) -> str: return f"sec:ipfail:{ip}"

    async def is_locked(self, email: str) -> bool:
        try:
            return bool(await self.redis.exists(self._lock_key(email)))
        except Exception as exc:  # noqa: BLE001 — fail-open
            logger.warning("lockout check unavailable (%s)", exc)
            return False

    async def record_failure(self, email: str, ip: str | None) -> LockState:
        try:
            fk = self._fail_key(email)
            failures = await self.redis.incr(fk)
            if failures == 1:
                await self.redis.expire(fk, self.s.login_failure_window_seconds)
            ip_failures = 0
            if ip:
                ik = self._ipfail_key(ip)
                ip_failures = await self.redis.incr(ik)
                if ip_failures == 1:
                    await self.redis.expire(ik, self.s.login_failure_window_seconds)
            locked = failures >= self.s.login_max_failures
            if locked:
                await self.redis.set(self._lock_key(email), "1", ex=self.s.login_lockout_seconds)
            return LockState(locked, failures, ip_failures, self.s.login_lockout_seconds)
        except Exception as exc:  # noqa: BLE001 — fail-open
            logger.warning("failure tracking unavailable (%s)", exc)
            return LockState(False, 0, 0, self.s.login_lockout_seconds)

    async def clear(self, email: str) -> None:
        try:
            await self.redis.delete(self._fail_key(email), self._lock_key(email))
        except Exception as exc:  # noqa: BLE001
            logger.warning("failure clear unavailable (%s)", exc)

    async def ip_failures(self, ip: str) -> int:
        try:
            return int(await self.redis.get(self._ipfail_key(ip)) or 0)
        except Exception:  # noqa: BLE001
            return 0
