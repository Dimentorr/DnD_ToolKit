"""Название: user.py

Путь: backend/db/model/user.py
Автор: stepapetruk@ya.ru
Дата: [04.05.2026]::2026-May-Monday
Описание:

Описание файла.
"""

from uuid import UUID

from backend.models.base import BasePydanticModel


class User(BasePydanticModel):
    """pydantic-модель объекта user"""

    uuid: UUID
    name: str
    password: str | None = None


class UserCreated(BasePydanticModel):
    """pydantic-модель объекта user для регистрации"""

    name: str
    password: str
