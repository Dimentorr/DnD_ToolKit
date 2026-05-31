"""Название: ruleset.py

Путь: backend/db/orm/ruleset.py
Автор: stepapetruk@ya.ru
Дата: [31.05.2026]::2026-May-Sunday
Описание:

Описание файла.
"""

import datetime
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, String, Text, func
from sqlalchemy import UUID as SqlUUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.orm.base import Base
from backend.models.ruleset import Status


class Ruleset(Base):
    """ORM-модель таблицы rulesets"""

    __tablename__ = "rulesets"

    uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    owner_uuid: Mapped[UUID | None] = mapped_column(
        SqlUUID,
        ForeignKey(
            "users.uuid",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    parent_uuid: Mapped[UUID | None] = mapped_column(
        SqlUUID,
        ForeignKey(
            "rulesets.uuid",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Описание книги правил",
    )

    version: Mapped[str] = mapped_column(
        String(24),
        default="0.0.1",
        nullable=False,
    )
    status: Mapped[Status] = mapped_column(
        String,
        default=Status.InWork,
        nullable=False,
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        comment="общедоступная книга правил",
        default=False,
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
