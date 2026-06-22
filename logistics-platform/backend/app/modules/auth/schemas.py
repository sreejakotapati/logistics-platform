"""Auth API contracts (request/response schemas)."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


# ----------------------------------------------------------------- requests
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    organization_name: str = Field(min_length=1, max_length=200)
    organization_slug: str | None = Field(default=None, max_length=80)


class ProvisionRequest(BaseModel):
    organization_name: str = Field(min_length=1, max_length=200)
    organization_slug: str | None = Field(default=None, max_length=80)
    admin_email: EmailStr
    admin_full_name: str = Field(min_length=1, max_length=200)
    admin_password: str | None = Field(default=None, min_length=10, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PasswordResetRequestRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=16, max_length=512)
    new_password: str = Field(min_length=10, max_length=128)


class EmailVerifyRequest(BaseModel):
    token: str = Field(min_length=16, max_length=512)


class EmailVerifyResendRequest(BaseModel):
    email: EmailStr


# ---------------------------------------------------------------- responses
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class MembershipSummary(BaseModel):
    organization_id: uuid.UUID
    name: str
    slug: str
    status: str
    is_primary: bool


class MeResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    status: str
    email_verified: bool
    active_organization_id: uuid.UUID | None
    organizations: list[MembershipSummary]


class ProvisionResponse(BaseModel):
    organization_id: uuid.UUID
    admin_user_id: uuid.UUID
    admin_status: str
    message: str


class SwitchOrgResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    active_organization_id: uuid.UUID


class MessageResponse(BaseModel):
    message: str
