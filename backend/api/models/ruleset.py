"""Название: ruleset.py

Путь: backend/api/models/ruleset.py
Автор: stepapetruk@ya.ru
Дата: [31.05.2026]::2026-May-Sunday
Описание:

Описание файла.
"""

from typing import Any
from uuid import UUID

from pydantic import Field

from backend.models.base import BasePydanticModel
from backend.models.ruleset import Status


class APIRulesetCreated(BasePydanticModel):
    """Pydantic-модель книги правил для создания записи."""

    owner_uuid: UUID | None = None
    parent_uuid: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str = "Описание книги правил"
    version: str = Field(default="0.0.1", min_length=1, max_length=24)
    status: Status = Status.InWork
    is_public: bool = False

    def as_dict(self) -> dict[str, Any]:
        """Привести модель к словарю."""
        return self.model_dump(mode="json")
