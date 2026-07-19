"""Название: race.py

Путь: backend/api/models/race.py
Автор: stepapetruk@ya.ru
Дата: [19.07.2026]::2026-July-Sunday
Описание:

API-модели рас персонажей.
"""

from typing import Any
from uuid import UUID

from pydantic import Field

from backend.models.base import BasePydanticModel


class APIRaceCreated(BasePydanticModel):
    """Данные для создания расы через API."""

    ruleset_uuid: UUID
    parent_uuid: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)

    def as_dict(self) -> dict[str, Any]:
        """Преобразовать модель в JSON-совместимый словарь."""
        return self.model_dump(mode="json")
