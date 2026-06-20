"""Generic async repository (data-access layer).

Concrete repositories (Sprint 2+) subclass this with a specific model. The repository
owns queries; it does NOT own transactions (the service layer does).
"""
from __future__ import annotations

from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, entity_id: Any) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def list(self, *, limit: int = 20, offset: int = 0,
                   filters: dict[str, Any] | None = None) -> Sequence[ModelT]:
        stmt = select(self.model)
        for field, value in (filters or {}).items():
            stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, *, filters: dict[str, Any] | None = None) -> int:
        stmt = select(func.count()).select_from(self.model)
        for field, value in (filters or {}).items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, **values: Any) -> ModelT:
        instance = self.model(**values)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: ModelT, **values: Any) -> ModelT:
        for field, value in values.items():
            setattr(instance, field, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    async def soft_delete(self, instance: ModelT) -> ModelT:
        from datetime import datetime, timezone

        if hasattr(instance, "deleted_at"):
            setattr(instance, "deleted_at", datetime.now(timezone.utc))
            await self.session.flush()
        return instance
