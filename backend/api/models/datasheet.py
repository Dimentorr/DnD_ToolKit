"""Название: datasheet.py

Путь: backend/api/models/datasheet.py
Автор: stepapetruk@ya.ru
Дата: [07.05.2026]::2026-May-Thursday
Описание:

Описание файла.
"""

from uuid import UUID

from backend.models.base import BasePydanticModel
from backend.models.datasheet import Features, Inventory, Stats, Wallet


class APIDatasheetCreated(BasePydanticModel):
    """pydantic-модель объекта datasheet для регистрации"""

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
