"""Async SQLAlchemy engine, session factory, tenancy context, and health."""
from __future__ import annotations

import logging
from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings

logger = logging.getLogger("app.db")

_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None
_system_engine = None
_system_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_engine(settings: Settings) -> None:
    global _engine, _sessionmaker
    _engine = create_async_engine(
        settings.database_url,
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=settings.db_pool_pre_ping,
    )
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    logger.info("Database engine initialized")


def init_system_engine(settings: Settings) -> None:
    """Identity-plane engine (BYPASSRLS role) for auth/provisioning and cross-org identity reads.

    Falls back to the runtime DSN when SYSTEM_DATABASE_URL is unset (dev convenience).
    """
    global _system_engine, _system_sessionmaker
    dsn = settings.system_database_url or settings.database_url
    _system_engine = create_async_engine(
        dsn, echo=settings.db_echo, pool_pre_ping=settings.db_pool_pre_ping
    )
    _system_sessionmaker = async_sessionmaker(
        _system_engine, expire_on_commit=False, class_=AsyncSession
    )
    logger.info("Identity-plane engine initialized")


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None


async def dispose_system_engine() -> None:
    global _system_engine, _system_sessionmaker
    if _system_engine is not None:
        await _system_engine.dispose()
        _system_engine = None
        _system_sessionmaker = None


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        raise RuntimeError("Database is not initialized. Did the app lifespan run?")
    return _sessionmaker


def get_system_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _system_sessionmaker is None:
        raise RuntimeError("Identity-plane engine is not initialized. Did the app lifespan run?")
    return _system_sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an RLS-enforced AsyncSession (app_user)."""
    async with get_sessionmaker()() as session:
        yield session


async def get_system_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an identity-plane AsyncSession (BYPASSRLS).

    Use ONLY for auth/provisioning and cross-org identity reads — never for tenant business data.
    """
    async with get_system_sessionmaker()() as session:
        yield session


async def set_current_org_id(session: AsyncSession, organization_id: str) -> None:
    """Set the per-request active organization for RLS (decision #1).

    Must be called inside the request transaction once auth lands (Sprint 2);
    `app.current_org_id()` reads this GUC and RLS policies enforce it.
    """
    await session.execute(
        text("SELECT set_config('app.current_org_id', :oid, true)"), {"oid": str(organization_id)}
    )


async def check_database() -> bool:
    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database health check failed: %s", exc)
        return False
