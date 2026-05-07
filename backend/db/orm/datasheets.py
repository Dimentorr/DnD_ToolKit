"""Название: datasheets.py

Путь: backend\ORM\datasheets.py
Автор: stepapetruk@ya.ru
Дата: [03.05.2026]::2026-May-Sunday
Описание:

Описание файла.
"""

import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, TIMESTAMP, ForeignKey, String, func
from sqlalchemy import UUID as SqlUUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.orm.base import Base
from backend.models.datasheet import Features, Stats, Wallet


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
    name: Mapped[str] = mapped_column(String, nullable=False)

    stats: Mapped[dict[str, int]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=lambda: Stats().as_dict(),
        nullable=False,
    )

    wallet: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=lambda: Wallet().as_dict(),
        comment="кошель персонажа",
        nullable=False,
    )
    features: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=lambda: Features().as_dict(),
        comment="черты персонажа",
        nullable=False,
    )

    inventory: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON),
        default=dict,
        comment="инвентарь персонажа",
        nullable=False,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
