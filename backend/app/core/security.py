"""Security primitives: password hashing and low-level JWT helpers.

NOTE: This is the security FOUNDATION only. Authentication flows (login, token issuance
tied to users, refresh rotation, org-switch) are implemented in Sprint 2.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except Exception:
        return False


def encode_token(payload: dict, *, secret: str, algorithm: str = "HS256",
                 expires_delta: timedelta | None = None) -> str:
    to_encode = dict(payload)
    now = datetime.now(timezone.utc)
    to_encode.setdefault("iat", now)
    if expires_delta is not None:
        to_encode["exp"] = now + expires_delta
    return jwt.encode(to_encode, secret, algorithm=algorithm)


def decode_token(token: str, *, secret: str, algorithms: list[str] | None = None) -> dict:
    return jwt.decode(token, secret, algorithms=algorithms or ["HS256"])
