"""Token primitives — pure helpers (no DB).

Access tokens are short-lived JWTs (HS256). Refresh tokens are high-entropy opaque strings; only their
SHA-256 hash is ever stored. Rotation/reuse orchestration lives in the service layer.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

from app.core.config import Settings
from app.core.security import decode_token, encode_token


@dataclass(frozen=True)
class AccessClaims:
    """Typed view of the access-token payload (the JWT contract)."""

    sub: str          # user id
    org: str | None   # active organization id (None only if the user has no membership)
    jti: str
    type: str
    raw: dict

    @property
    def is_access(self) -> bool:
        return self.type == "access"


def parse_access_claims(payload: dict) -> AccessClaims:
    return AccessClaims(
        sub=payload.get("sub", ""),
        org=payload.get("org"),
        jti=payload.get("jti", ""),
        type=payload.get("type", ""),
        raw=payload,
    )


def new_jti() -> str:
    return uuid.uuid4().hex


def issue_access_token(settings: Settings, *, user_id: str, org_id: str | None) -> tuple[str, int]:
    """Return (jwt, expires_in_seconds). `org` claim is the active org (primary until S2 org-switch)."""
    ttl = timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": str(user_id),
        "org": str(org_id) if org_id else None,
        "type": "access",
        "jti": new_jti(),
    }
    token = encode_token(
        payload, secret=settings.jwt_secret, algorithm=settings.jwt_algorithm, expires_delta=ttl
    )
    return token, int(ttl.total_seconds())


def decode_access_token(settings: Settings, token: str) -> dict:
    """Decode + validate signature/expiry; raises on invalid. Caller checks `type`."""
    return decode_token(token, secret=settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def generate_refresh_secret() -> str:
    """48 bytes of entropy, URL-safe."""
    return secrets.token_urlsafe(48)


def hash_token(raw: str) -> str:
    """SHA-256 hex. Sufficient for high-entropy random tokens (no salt needed)."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_url_token() -> str:
    """Opaque token for email-verification / password-reset links."""
    return secrets.token_urlsafe(32)
