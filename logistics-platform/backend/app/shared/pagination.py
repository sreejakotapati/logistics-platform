"""Pagination params dependency and a generic page envelope."""
from __future__ import annotations

from typing import Generic, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def limit(self) -> int:
        return self.page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(cls, items: Sequence[T], total: int, params: PaginationParams) -> "Page[T]":
        pages = (total + params.page_size - 1) // params.page_size if params.page_size else 0
        return cls(items=items, total=total, page=params.page,
                   page_size=params.page_size, pages=pages)
