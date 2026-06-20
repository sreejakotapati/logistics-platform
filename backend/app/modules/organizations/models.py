"""Organizations-module ORM. Core entity mappings (User/Organization/UserOrganization/Role) live in
`auth.models` and are reused here; this file adds only the invitation table.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

# Re-export the shared core mappings so this module has a single import surface.
from app.modules.auth.models import (  # noqa: F401
    Organization,
    Role,
    User,
    UserOrganization,
)


class Invitation(Base):
    __tablename__ = "org_invitations"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("app.uuid_generate_v7()")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    role_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("roles.id"))
    invited_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
