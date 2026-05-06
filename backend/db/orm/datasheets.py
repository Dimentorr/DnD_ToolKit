"""Название: datasheets.py

Путь: backend\ORM\datasheets.py
Автор: stepapetruk@ya.ru
Дата: [03.05.2026]::2026-May-Sunday
Описание:

Описание файла.
"""

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy import UUID as SqlUUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.orm.base import Base
from backend.models.base import BasePydanticModel


class Wallet(BasePydanticModel):
    """Модель кошелька персонажа"""

    platina: int = 0
    electrum: int = 0
    gold: int = 0
    silver: int = 0
    copper: int = 0

    def as_dict(self):
        """Привести модель к словарю

        Returns: `dict`
        """
        return self.model_dump()


class Skills(BasePydanticModel):
    """Модель новыков персонажа"""

    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def as_dict(self) -> dict:
        """Привести модель к словарю

        Returns: `dict`
        """
        return self.model_dump()


class Datasheet(Base):
    """ORM-модель таблицы datasheets"""

    __tablename__ = "datasheets"

    uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    user_uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        ForeignKey("users.uuid"),
        nullable=False,
    )
    name_character: Mapped[str] = mapped_column(String, nullable=False)

    skills: Mapped[dict[str, int]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=lambda: Skills().as_dict(),
        nullable=False,
    )

    wallet: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=lambda: Wallet().as_dict(),
        comment="кошель персонажа",
        nullable=False,
    )
    inventory: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict,
        comment="инвентарь персонажа",
        nullable=False,
    )
