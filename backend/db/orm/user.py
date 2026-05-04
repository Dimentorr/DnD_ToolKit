"""Название: user.py

Путь: backend/db/orm/user.py
Автор: stepapetruk@ya.ru
Дата: [03.05.2026]::2026-May-Sunday
Описание:

Описание файла.
"""

from uuid import UUID, uuid4

from sqlalchemy import UUID as SqlUUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.orm.base import Base


class User(Base):
    """ORM-модель таблицы users"""

    __tablename__ = "users"

    uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
