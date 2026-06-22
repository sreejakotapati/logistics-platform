"""Audit services: query/search/timeline, actor & entity tracking, export, and retention.

Read-only. Tenancy is enforced by the RLS session passed in. Cursors are opaque base64 of
`{created_at}|{id}` for stable keyset pagination over the append-only log.
"""
from __future__ import annotations

import base64
import csv
import io
import json
import uuid
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.core.exceptions import ValidationError
from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditFilters, AuditRepository

_RETENTION_POLICY = (
    "Immutable append-only log. Retention is enforced by archival, never row deletion: records older "
    "than the window are exported to cold storage and (when monthly RANGE partitioning is adopted) the "
    "aged partition is DETACHed at the infra tier. No UPDATE or DELETE is ever issued against live rows."
)


def encode_cursor(created_at: datetime, row_id: uuid.UUID) -> str:
    return base64.urlsafe_b64encode(f"{created_at.isoformat()}|{row_id}".encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        iso, rid = raw.rsplit("|", 1)
        return datetime.fromisoformat(iso), uuid.UUID(rid)
    except Exception as exc:  # noqa: BLE001
        raise ValidationError("Invalid pagination cursor") from exc


def _row(a: AuditLog) -> dict:
    return {
        "id": a.id, "organization_id": a.organization_id, "actor_user_id": a.actor_user_id,
        "action": a.action, "entity_type": a.entity_type, "entity_id": a.entity_id,
        "metadata": a.meta or {}, "ip_address": a.ip_address, "user_agent": a.user_agent,
        "created_at": a.created_at,
    }


class AuditService:
    def __init__(self, session, settings: Settings) -> None:
        self.repo = AuditRepository(session)
        self.settings = settings

    def _limit(self, limit: int | None) -> int:
        if limit is None:
            return self.settings.audit_default_page_size
        if limit < 1 or limit > self.settings.audit_max_page_size:
            raise ValidationError(f"limit must be between 1 and {self.settings.audit_max_page_size}")
        return limit

    async def query(
        self, f: AuditFilters, *, limit: int | None, cursor: str | None,
        include_total: bool = False, ascending: bool = False,
    ) -> tuple[list[dict], str | None, int | None]:
        lim = self._limit(limit)
        cur = decode_cursor(cursor) if cursor else None
        rows, has_more = await self.repo.page(f, limit=lim, cursor=cur, ascending=ascending)
        next_cursor = encode_cursor(rows[-1].created_at, rows[-1].id) if (has_more and rows) else None
        total = await self.repo.count(f) if include_total else None
        return [_row(r) for r in rows], next_cursor, total

    async def timeline(
        self, f: AuditFilters, *, limit: int | None, cursor: str | None
    ) -> tuple[list[dict], str | None]:
        rows, next_cursor, _ = await self.query(f, limit=limit, cursor=cursor, ascending=False)
        buckets: "OrderedDict[str, list[dict]]" = OrderedDict()
        for r in rows:
            day = r["created_at"].date().isoformat()
            buckets.setdefault(day, []).append(r)
        return (
            [{"date": d, "count": len(items), "items": items} for d, items in buckets.items()],
            next_cursor,
        )


class ExportService:
    """Builds CSV/JSON exports. The builder is a pure async generator so a background worker can stream
    it to object storage; the synchronous endpoint uses the same path bounded by `audit_export_max_rows`."""

    _COLUMNS = [
        "id", "created_at", "organization_id", "actor_user_id", "action",
        "entity_type", "entity_id", "ip_address", "user_agent", "metadata",
    ]

    def __init__(self, session, settings: Settings) -> None:
        self.repo = AuditRepository(session)
        self.settings = settings

    async def build(self, f: AuditFilters, fmt: str) -> tuple[str, str, int]:
        if fmt not in ("csv", "json"):
            raise ValidationError("format must be 'csv' or 'json'")
        rows: list[dict] = []
        async for a in self.repo.iter_export(f, max_rows=self.settings.audit_export_max_rows):
            rows.append(_row(a))
        if fmt == "csv":
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=self._COLUMNS)
            writer.writeheader()
            for r in rows:
                writer.writerow({
                    **{k: ("" if r[k] is None else r[k]) for k in self._COLUMNS if k != "metadata"},
                    "metadata": json.dumps(r["metadata"]),
                })
            return buf.getvalue(), "text/csv", len(rows)
        payload = json.dumps(
            [{**r, "id": str(r["id"]), "created_at": r["created_at"].isoformat(),
              "organization_id": str(r["organization_id"]) if r["organization_id"] else None,
              "actor_user_id": str(r["actor_user_id"]) if r["actor_user_id"] else None,
              "entity_id": str(r["entity_id"]) if r["entity_id"] else None} for r in rows],
            default=str,
        )
        return payload, "application/json", len(rows)


class RetentionService:
    def __init__(self, session, settings: Settings) -> None:
        self.repo = AuditRepository(session)
        self.settings = settings

    def cutoff(self) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=self.settings.audit_retention_days)

    async def preview(self, f: AuditFilters) -> dict:
        cutoff = self.cutoff()
        total = await self.repo.count(f)
        oldest, newest = await self.repo.bounds(f)
        archivable = await self.repo.count(
            AuditFilters(**{**f.__dict__, "date_to": cutoff})
        )
        return {
            "retention_days": self.settings.audit_retention_days, "cutoff": cutoff,
            "total_records": total, "archivable_records": archivable,
            "oldest": oldest, "newest": newest, "policy": _RETENTION_POLICY,
        }
