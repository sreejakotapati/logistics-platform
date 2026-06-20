"""Application bootstrap: factory, lifespan, middleware, routers."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core import redis as redis_module
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db import session as db_module
from app.middleware.logging import AccessLogMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.modules.security.middleware import (
    CsrfMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.modules.tenancy.middleware import TenancyContextMiddleware

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Initialize connection layers (objects only; first connect is lazy).
    db_module.init_engine(settings)
    db_module.init_system_engine(settings)
    redis_module.init_redis(settings)
    if settings.bootstrap_superadmin_email:
        try:
            from app.modules.rbac.service import PlatformAdminService

            async with db_module.get_system_sessionmaker()() as s:
                promoted = await PlatformAdminService(s, None).ensure_by_email(
                    settings.bootstrap_superadmin_email
                )
                await s.commit()
            if promoted:
                logger.info("Bootstrapped platform admin: %s", settings.bootstrap_superadmin_email)
        except Exception as exc:  # noqa: BLE001 — never block startup on bootstrap
            logger.warning("Platform-admin bootstrap skipped: %s", exc)
    logger.info("Application started", extra={"env": settings.app_env, "version": __version__})
    try:
        yield
    finally:
        await db_module.dispose_engine()
        await db_module.dispose_system_engine()
        await redis_module.close_redis()
        logger.info("Application stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Logistics Management Platform API",
        version=__version__,
        debug=settings.app_debug,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware (outermost first): CORS -> security headers -> rate limit -> CSRF -> access log -> request id.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(CsrfMiddleware, settings=settings)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TenancyContextMiddleware)

    register_exception_handlers(app)

    # Root-level health/readiness + versioned API surface.
    app.include_router(health_router)
    app.include_router(api_router, prefix=settings.api_base_path)

    return app


app = create_app()
