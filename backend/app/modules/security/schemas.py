"""Security API contracts."""
from __future__ import annotations

import uuid

from pydantic import BaseModel


class PasswordPolicyOut(BaseModel):
    min_length: int
    max_length: int
    min_character_classes: int
    character_classes: list[str]
    blocks_common_passwords: bool


class SessionOut(BaseModel):
    family_id: uuid.UUID
    issued_at: str
    expires_at: str
    ip_address: str | None
    user_agent: str | None
    active_organization_id: uuid.UUID | None
    current: bool


class SessionListOut(BaseModel):
    sessions: list[SessionOut]


class RevokeResultOut(BaseModel):
    revoked: int


class MessageOut(BaseModel):
    message: str


class AbuseSnapshotOut(BaseModel):
    flagged_ips: list[dict]
    locked_accounts: int
    thresholds: dict
