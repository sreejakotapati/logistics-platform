"""Generic service base (business-logic layer).

The service owns the unit-of-work (commit/rollback) and business rules; it delegates
persistence to a repository. Concrete services (Sprint 2+) subclass this.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.base_repository import BaseRepository

ModelT = TypeVar("ModelT")


class BaseService(Generic[ModelT]):
    def __init__(self, session: AsyncSession, repository: BaseRepository[ModelT]) -> None:
        self.session = session
        self.repository = repository

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
