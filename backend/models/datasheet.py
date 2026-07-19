"""Название: datasheet.py

Путь: backend/models/datasheet.py
Автор: stepapetruk@ya.ru
Дата: [07.05.2026]::2026-May-Thursday
Описание:

Описание файла.
"""

from typing import Annotated, Any
from uuid import UUID

from pydantic import Field

from backend.models.base import BasePydanticModel

NonNegativeInt = Annotated[int, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]
AbilityScore = Annotated[int, Field(ge=1)]


class Wallet(BasePydanticModel):
    """Модель кошелька персонажа"""

    platina: NonNegativeInt = 0
    electrum: NonNegativeInt = 0
    gold: NonNegativeInt = 0
    silver: NonNegativeInt = 0
    copper: NonNegativeInt = 0

    def as_dict(self) -> dict[str, Any]:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class Stats(BasePydanticModel):
    """Модель характеристик персонажа"""

    strength: AbilityScore = 10
    dexterity: AbilityScore = 10
    constitution: AbilityScore = 10
    intelligence: AbilityScore = 10
    wisdom: AbilityScore = 10
    charisma: AbilityScore = 10

    def as_dict(self) -> dict[str, Any]:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class Features(BasePydanticModel):
    """Модель черт персонажа"""

    one: UUID | None = None
    four: UUID | None = None
    twelve: UUID | None = None
    nineteen: UUID | None = None

    def as_dict(self) -> dict[str, Any]:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")


class Item(BasePydanticModel):
    """Модель предмета в инвенторе персонажа"""

    uuid: UUID
    count: PositiveInt = 1
    description: str | None = Field(default=None, max_length=2_000)


class Inventory(BasePydanticModel):
    """Модель инвенторя персонажа"""

    data: list[Item] = Field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Привести модель к словарю"""
        return self.model_dump(mode="json")
