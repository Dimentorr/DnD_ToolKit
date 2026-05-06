"""Название: token.py

Путь: backend/db/model/token.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Модуль содержащий pydantic-модели токена.
"""

import datetime
from uuid import UUID

from backend.models.base import BasePydanticModel


class TokenCreated(BasePydanticModel):
    """Данные для создания токена.

    Attributes:
        user_uuid (UUID): UUID пользователя, которому принадлежит токен.
        token (str): токен в открытом виде. Перед сохранением в БД
            должен быть преобразован в детерминированный хеш.
    """

    user_uuid: UUID
    token: str


class TokenData(BasePydanticModel):
    """Данные refresh-токена из БД.

    Описывает запись таблицы tokens после чтения из БД. Используется при
    проверке refresh-токена, logout и refresh-token rotation.

    Attributes:
        uuid (UUID): UUID записи токена.
        user_uuid (UUID): UUID пользователя, которому принадлежит токен.
        token (str): Хеш refresh-токена, сохранённый в БД.
        expires_at (datetime.datetime): Дата и время истечения refresh-токена.
        created_at (datetime.datetime): Дата и время создания записи токена.
        updated_at (datetime.datetime): Дата и время последнего обновления записи.
        revoked_at (datetime.datetime | None): Дата и время отзыва токена.
            Если значение None, токен не был отозван.
    """

    uuid: UUID
    user_uuid: UUID
    token: str
    expires_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime
    revoked_at: datetime.datetime | None = None
