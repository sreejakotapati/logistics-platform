"""Liveness and readiness endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.redis import check_redis
from app.db.session import check_database
from app.shared.schemas import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    """Liveness: the process is up. Does not depend on DB/Redis."""
    return HealthStatus(status="ok")


@router.get("/ready")
async def ready() -> JSONResponse:
    """Readiness: dependencies (DB, Redis) are reachable."""
    db_ok = await check_database()
    redis_ok = await check_redis()
    ready_ = db_ok and redis_ok
    return JSONResponse(
        status_code=200 if ready_ else 503,
        content={"status": "ok" if ready_ else "not_ready",
                 "checks": {"database": db_ok, "redis": redis_ok}},
    )
