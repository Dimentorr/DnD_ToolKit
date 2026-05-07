"""Название: datasheet.py

Путь: backend/db/model/datasheet.py
Автор: stepapetruk@ya.ru
Дата: [07.05.2026]::2026-May-Thursday
Описание:

Описание файла.
"""

import datetime
from uuid import UUID

from backend.models.base import BasePydanticModel
from backend.models.datasheet import Features, Inventory, Stats, Wallet


class DatasheetCreated(BasePydanticModel):
    """pydantic-модель объекта datasheet для регистрации"""

    user_uuid: UUID
    name: str | None = None
    # uuid расы, расс покачто нет
    race: UUID | None = None
    stats: Stats = Stats()
    wallet: Wallet = Wallet()
    features: Features = Features()
    inventory: Inventory = Inventory()

    def as_dict(self) -> dict:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class DatasheetUpdated(BasePydanticModel):
    """pydantic-модель объекта datasheet для обновления"""

    uuid: UUID
    name: str | None = None
    # uuid расы, расс покачто нет
    race: UUID | None = None
    stats: Stats | None = None
    wallet: Wallet | None = None
    features: Features | None = None
    inventory: Inventory | None = None

    def as_dict(self) -> dict:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class Datasheet(DatasheetCreated):
    """pydantic-модель объекта datasheet"""

    uuid: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
