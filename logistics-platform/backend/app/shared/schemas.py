"""Base Pydantic schemas."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base for response schemas reading from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class HealthStatus(BaseModel):
    status: str


class ReadinessStatus(BaseModel):
    status: str
    checks: dict[str, bool]
