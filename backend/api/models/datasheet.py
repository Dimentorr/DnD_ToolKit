"""Название: datasheet.py

Путь: backend/api/models/datasheet.py
Автор: stepapetruk@ya.ru
Дата: [07.05.2026]::2026-May-Thursday
Описание:

Описание файла.
"""

from typing import Any
from uuid import UUID

from pydantic import Field

from backend.models.base import BasePydanticModel
from backend.models.datasheet import Features, Inventory, Stats, Wallet


class APIDatasheetCreated(BasePydanticModel):
    """pydantic-модель объекта datasheet для регистрации"""

    name: str = Field(min_length=1, max_length=255)
    ruleset_uuid: UUID
    # UUID выбранной расы.
    race: UUID | None = None
    stats: Stats = Field(default_factory=Stats)
    wallet: Wallet = Field(default_factory=Wallet)
    features: Features = Field(default_factory=Features)
    inventory: Inventory = Field(default_factory=Inventory)

    def as_dict(self) -> dict[str, Any]:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")
