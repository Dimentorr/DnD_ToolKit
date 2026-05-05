"""Название: token.py

Путь: backend/db/model/token.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Модуль содержащий pydantic-модели токена.
"""

from uuid import UUID

from backend.models.base import BasePydanticModel


class Token(BasePydanticModel):
    """tokens"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BasePydanticModel):
    """token-дата"""

    user_uuid: UUID
