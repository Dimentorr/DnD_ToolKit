"""Название: datasheet.py

Путь: backend/db/model/datasheet.py
Автор: stepapetruk@ya.ru
Дата: [07.05.2026]::2026-May-Thursday
Описание:

Описание файла.
"""

import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from backend.models.base import BasePydanticModel
from backend.models.datasheet import Features, Inventory, Stats, Wallet


class DatasheetCreated(BasePydanticModel):
    """pydantic-модель объекта datasheet для регистрации"""

    user_uuid: UUID
    ruleset_uuid: UUID
    name: str = Field(min_length=1, max_length=255)
    # UUID выбранной расы.
    race: UUID | None = None
    stats: Stats = Field(default_factory=Stats)
    wallet: Wallet = Field(default_factory=Wallet)
    features: Features = Field(default_factory=Features)
    inventory: Inventory = Field(default_factory=Inventory)

    def as_dict(self) -> dict[str, Any]:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class DatasheetUpdated(BasePydanticModel):
    """pydantic-модель объекта datasheet для обновления"""

    uuid: UUID
    name: str | None = Field(default=None, min_length=1, max_length=255)
    ruleset_uuid: UUID | None = None
    # UUID выбранной расы.
    race: UUID | None = None
    stats: Stats | None = None
    wallet: Wallet | None = None
    features: Features | None = None
    inventory: Inventory | None = None

    def as_dict(self) -> dict[str, Any]:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class Datasheet(DatasheetCreated):
    """pydantic-модель объекта datasheet"""

    ruleset_uuid: UUID | None = None
    uuid: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
