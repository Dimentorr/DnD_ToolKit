"""Название: ruleset.py

Путь: backend/db/model/ruleset.py
Автор: stepapetruk@ya.ru
Дата: [31.05.2026]::2026-May-Sunday
Описание:

Pydantic-модели книги правил.
"""

import datetime
from uuid import UUID

from backend.models.base import BasePydanticModel
from backend.models.ruleset import Status


class RulesetCreated(BasePydanticModel):
    """Pydantic-модель книги правил для создания записи."""

    owner_uuid: UUID | None = None
    parent_uuid: UUID | None = None
    name: str
    description: str = "Описание книги правил"
    version: str = "0.0.1"
    status: Status = Status.InWork
    is_public: bool = False

    def as_dict(self) -> dict:
        """Привести модель к словарю."""
        return self.model_dump(mode="json")


class RulesetUpdated(BasePydanticModel):
    """Pydantic-модель книги правил для частичного обновления записи."""

    uuid: UUID
    owner_uuid: UUID | None = None
    parent_uuid: UUID | None = None
    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: Status | None = None
    is_public: bool | None = None

    def as_dict(self) -> dict:
        """Привести только переданные поля модели к словарю."""
        return self.model_dump(
            mode="json",
            exclude_unset=True,
        )


class Ruleset(RulesetCreated):
    """Pydantic-модель книги правил."""

    uuid: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
