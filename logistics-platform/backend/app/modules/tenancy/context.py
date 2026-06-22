"""Per-request tenant context value object."""
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    user_id: uuid.UUID
    organization_id: uuid.UUID
