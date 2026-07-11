"""Shared API response wrappers."""

from app.core.schemas import PaginatedResponse


class PaginatedItems(PaginatedResponse):
    items: list
