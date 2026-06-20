"""Request-context middleware.

Decodes the access token ONCE per request and stashes the claims on `request.state`. It enforces
nothing (public routes carry no token) — enforcement lives in the tenant dependencies. The active org is
read only from the signed token here; it is never taken from headers, query, or body.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings
from app.modules.auth import tokens


class TenancyContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.auth_claims = None
        request.state.active_org_id = None

        authz = request.headers.get("authorization")
        if authz and authz.lower().startswith("bearer "):
            raw = authz.split(" ", 1)[1].strip()
            try:
                payload = tokens.decode_access_token(get_settings(), raw)
            except Exception:  # noqa: BLE001 — invalid/expired token; deps will 401 where required
                payload = None
            if payload and payload.get("type") == "access":
                request.state.auth_claims = payload
                request.state.active_org_id = payload.get("org")

        return await call_next(request)
