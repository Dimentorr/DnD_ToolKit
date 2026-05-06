"""Название: user.py

Путь: backend/db/model/user.py
Автор: stepapetruk@ya.ru
Дата: [04.05.2026]::2026-May-Monday
Описание:

Описание файла.
"""

import datetime
from uuid import UUID

from pydantic import EmailStr

from backend.models.base import BasePydanticModel


class User(BasePydanticModel):
    """pydantic-модель объекта user"""

    uuid: UUID
    name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    email: EmailStr | None = None
    password: str | None = None


class UserCreated(BasePydanticModel):
    """pydantic-модель объекта user для регистрации"""

    name: str
    email: EmailStr | None = None
    password: str
