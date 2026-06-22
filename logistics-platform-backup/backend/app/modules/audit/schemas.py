"""Audit API contracts."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID | None
    actor_user_id: uuid.UUID | None
    action: str
    entity_type: str | None
    entity_id: uuid.UUID | None
    metadata: dict
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AuditPage(BaseModel):
    items: list[AuditLogOut]
    next_cursor: str | None = None
    total: int | None = None


class TimelineBucket(BaseModel):
    date: str
    count: int
    items: list[AuditLogOut]


class AuditTimeline(BaseModel):
    buckets: list[TimelineBucket]
    next_cursor: str | None = None


class RetentionPreview(BaseModel):
    retention_days: int
    cutoff: datetime
    total_records: int
    archivable_records: int
    oldest: datetime | None
    newest: datetime | None
    policy: str


class ExportJob(BaseModel):
    status: str
    format: str
    row_count: int
    note: str
