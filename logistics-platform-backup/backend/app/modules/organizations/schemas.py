"""Users & Organizations API contracts + validation rules."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

GSTIN_PATTERN = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"


# ----------------------------------------------------------- organizations
class OrganizationProfile(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    legal_name: str | None = None
    gstin: str | None = None
    country_code: str | None = None
    currency: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    website: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None


class OrganizationProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    legal_name: str | None = Field(default=None, max_length=200)
    gstin: str | None = Field(default=None, pattern=GSTIN_PATTERN)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=200)
    address_line1: str | None = Field(default=None, max_length=200)
    address_line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)


class OrganizationSettings(BaseModel):
    settings: dict


class OrganizationSettingsUpdate(BaseModel):
    settings: dict = Field(description="Keys to merge into the org settings bag")


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=80)


class OrganizationSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    is_primary: bool
    membership_status: str


# --------------------------------------------------------------- members
class MemberSummary(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    full_name: str | None
    membership_status: str
    is_primary: bool


class MemberUpdate(BaseModel):
    status: str = Field(pattern=r"^(active|suspended)$")


# ----------------------------------------------------------- invitations
class InvitationCreate(BaseModel):
    email: EmailStr
    role_id: uuid.UUID | None = None


class InvitationSummary(BaseModel):
    id: uuid.UUID
    email: EmailStr
    status: str
    role_id: uuid.UUID | None
    expires_at: str


class InvitationPreview(BaseModel):
    organization_id: uuid.UUID
    organization_name: str
    email: EmailStr
    status: str
    expired: bool


# ----------------------------------------------------------------- users
class UserProfile(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    status: str
    email_verified: bool


class UserProfileUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)


class MessageResponse(BaseModel):
    message: str
