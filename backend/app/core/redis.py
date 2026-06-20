"""Async Redis client lifecycle and health.

A single async client (connection pool) created at startup and reused.
Cache/session/pubsub/rate-limit helpers are added in later sprints.
"""
from __future__ import annotations

import logging
from typing import AsyncIterator

import redis.asyncio as aioredis

from app.core.config import Settings

logger = logging.getLogger("app.redis")

_client: aioredis.Redis | None = None


def init_redis(settings: Settings) -> None:
    global _client
    _client = aioredis.from_url(
        settings.redis_url, decode_responses=True, health_check_interval=30
    )
    logger.info("Redis client initialized", extra={"url": settings.redis_url})


def get_client() -> aioredis.Redis:
    if _client is None:
        raise RuntimeError("Redis is not initialized. Did the app lifespan run?")
    return _client


async def get_redis() -> AsyncIterator[aioredis.Redis]:
    """FastAPI dependency yielding the shared Redis client."""
    yield get_client()


async def check_redis() -> bool:
    try:
        return bool(await get_client().ping())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis health check failed: %s", exc)
        return False


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
