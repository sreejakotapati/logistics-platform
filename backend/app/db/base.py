"""Declarative base and reusable column mixins.

These define HOW future tables are shaped (UUIDv7 PK, audit columns, soft delete,
optimistic locking) — they do NOT create any tables. Business/entity tables are
added from Sprint 2 and must inherit the appropriate mixins.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, MetaData, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("app.uuid_generate_v7()"),
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditMixin:
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VersionMixin:
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("1"))


class FoundationBase(
    Base, UUIDPrimaryKeyMixin, TimestampMixin, AuditMixin, SoftDeleteMixin, VersionMixin
):
    """Convenience base for org-scoped business tables (Sprint 2+).

    Concrete tables additionally declare ``organization_id`` and call
    ``app.enable_org_rls('public.<table>')`` in their migration.
    """

    __abstract__ = True
