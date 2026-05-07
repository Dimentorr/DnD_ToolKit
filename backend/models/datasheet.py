"""Название: datasheet.py

Путь: backend/models/datasheet.py
Автор: stepapetruk@ya.ru
Дата: [07.05.2026]::2026-May-Thursday
Описание:

Описание файла.
"""

from uuid import UUID

from pydantic import Field

from backend.models.base import BasePydanticModel


class Wallet(BasePydanticModel):
    """Модель кошелька персонажа"""

    platina: int = 0
    electrum: int = 0
    gold: int = 0
    silver: int = 0
    copper: int = 0

    def as_dict(self):
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class Stats(BasePydanticModel):
    """Модель характеристик персонажа"""

    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def as_dict(self) -> dict:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class Features(BasePydanticModel):
    """Модель черт персонажа"""

    one: UUID | None = None
    four: UUID | None = None
    twelve: UUID | None = None
    nineteen: UUID | None = None

    def as_dict(self) -> dict:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class Item(BasePydanticModel):
    """Модель предмета в инвенторе персонажа"""

    uuid: UUID
    count: int = 1
    description: str | None = None


class Inventory(BasePydanticModel):
    """Модель инвенторя персонажа"""

    data: list[Item] = Field(default_factory=list)

    def as_dict(self) -> dict:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")
