"""Security middleware: response hardening headers, Redis rate limiting, and CSRF origin verification.

Design constraints (S2-T8): no breaking API changes, no weakening of existing controls, everything
configurable, and every security decision audited. Middlewares fail-open on Redis errors (availability),
because the underlying password/token/RLS controls are never bypassed.
"""
from __future__ import annotations

from urllib.parse import urlparse

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from app.core.config import Settings
from app.core.logging import request_id_ctx
from app.core.redis import get_client
from app.modules.security.abuse import AbuseMonitor
from app.modules.security.audit import emit_security_event
from app.modules.security.limiter import RateLimiter

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
_SKIP_PREFIXES = ("/health", "/docs", "/redoc", "/openapi.json")
_DOCS_PREFIXES = ("/docs", "/redoc", "/openapi.json")


def _envelope(status_code: int, code: str, message: str, **details) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message,
                           "details": details, "request_id": request_id_ctx.get()}},
    )


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _origin_of(value: str) -> str | None:
    try:
        p = urlparse(value)
        if not p.scheme or not p.netloc:
            return None
        return f"{p.scheme}://{p.netloc}"
    except Exception:  # noqa: BLE001
        return None


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds hardening headers to every response. CSP is skipped for the API docs (Swagger needs a CDN)."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.s = settings

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if not self.s.security_headers_enabled:
            return response
        h = response.headers
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", self.s.security_frame_options)
        h.setdefault("Referrer-Policy", self.s.security_referrer_policy)
        h.setdefault("Permissions-Policy", self.s.security_permissions_policy)
        h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        h.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        if not request.url.path.startswith(_DOCS_PREFIXES):
            h.setdefault("Content-Security-Policy", self.s.security_csp)
        if self.s.security_hsts_enabled and self.s.is_production:
            h.setdefault(
                "Strict-Transport-Security",
                f"max-age={self.s.security_hsts_max_age}; includeSubDomains; preload",
            )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP global limit + tighter limit on auth-sensitive POSTs. Blocks are audited and feed abuse
    monitoring. Fail-open on Redis errors."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.s = settings
        self._auth_prefix = f"{settings.api_base_path}/auth"

    async def dispatch(self, request: Request, call_next):
        if not self.s.rate_limit_enabled or request.method == "OPTIONS" \
                or request.url.path.startswith(_SKIP_PREFIXES):
            return await call_next(request)

        ip = _client_ip(request)
        limiter = RateLimiter(get_client())
        window = self.s.rate_limit_window_seconds

        result = await limiter.hit("global", ip, limit=self.s.rate_limit_global_per_minute, window=window)
        scope = "global"
        if result.allowed and request.method == "POST" and request.url.path.startswith(self._auth_prefix):
            result = await limiter.hit("auth", ip, limit=self.s.rate_limit_auth_per_minute, window=window)
            scope = "auth"

        if not result.allowed:
            await self._on_block(request, ip, scope)
            resp = _envelope(429, "rate_limited", "Too many requests. Please slow down.", scope=scope)
            resp.headers["Retry-After"] = str(result.retry_after)
            resp.headers["RateLimit-Limit"] = str(result.limit)
            resp.headers["RateLimit-Remaining"] = "0"
            return resp

        response = await call_next(request)
        response.headers.setdefault("RateLimit-Remaining", str(result.remaining))
        return response

    async def _on_block(self, request: Request, ip: str, scope: str) -> None:
        monitor = AbuseMonitor(get_client(), self.s)
        blocks = await monitor.record_block(ip)
        await emit_security_event(
            self.s, action="security.rate_limited", entity_type="security",
            metadata={"scope": scope, "path": request.url.path, "method": request.method, "blocks": blocks},
            ip=ip, user_agent=request.headers.get("user-agent"),
        )
        if blocks >= self.s.abuse_alert_threshold:
            await monitor.flag(ip)
            await emit_security_event(
                self.s, action="security.abuse_detected", entity_type="security",
                metadata={"ip": ip, "blocks": blocks, "window_seconds": self.s.rate_limit_window_seconds},
                ip=ip,
            )


class CsrfMiddleware(BaseHTTPMiddleware):
    """Origin/Referer verification for cookie-authenticated unsafe requests.

    The refresh token is an httpOnly cookie, so it is an ambient credential — the CSRF vector. A malicious
    cross-site POST WILL carry an Origin header naming the attacker's site, so we reject unsafe requests
    that present the refresh cookie with a disallowed Origin/Referer. Requests without an Origin (curl,
    native apps, server-to-server) are not browser-CSRF and are allowed. This needs NO client change — the
    SPA's same-origin requests already send an allowed Origin — so it is not a breaking API change.
    """

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.s = settings
        allowed = settings.csrf_allowed_origins or [*settings.cors_origins, settings.frontend_base_url]
        self.allowed = {_origin_of(o) or o for o in allowed}

    async def dispatch(self, request: Request, call_next):
        if (not self.s.csrf_protection_enabled or request.method in _SAFE_METHODS
                or self.s.refresh_cookie_name not in request.cookies):
            return await call_next(request)

        origin_header = request.headers.get("origin") or request.headers.get("referer")
        if origin_header:
            origin = _origin_of(origin_header)
            if origin not in self.allowed:
                await emit_security_event(
                    self.s, action="security.csrf_blocked", entity_type="security",
                    metadata={"origin": origin_header, "path": request.url.path, "method": request.method},
                    ip=_client_ip(request), user_agent=request.headers.get("user-agent"),
                )
                return _envelope(403, "csrf_failed", "Cross-origin request rejected.")
        return await call_next(request)
