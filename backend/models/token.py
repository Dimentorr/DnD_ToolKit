"""Название: token.py

Путь: backend/models/token.py
Автор: stepapetruk@ya.ru
Дата: [06.05.2026]::2026-May-Wednesday
Описание:

Модуль моделей токенов.
"""

from enum import StrEnum, auto
from uuid import UUID

from backend.models.base import BasePydanticModel


class UserRole(StrEnum):
    """Возможные роли в приложении"""

    USER = auto()
    MODERATOR = auto()
    ADMIN = auto()


class CookieTokenData(BasePydanticModel):
    """Данные пользователя, в JWT-токене cookie.

    Attrs:
        user_uuid (UUID): UUID пользователя из поля `sub` JWT payload.
        role (str): Роль пользователя из поля `scope`.
        token_type (str): Тип токена.
    """

    user_uuid: UUID
    role: UserRole
    token_type: str
