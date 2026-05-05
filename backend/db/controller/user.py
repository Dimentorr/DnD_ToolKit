"""Название: user.py

Путь: backend/db/controller/user.py
Автор: stepapetruk@ya.ru
Дата: [04.05.2026]::2026-May-Monday
Описание:

Описание файла.
"""

import uuid
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.base import Database
from backend.db.model.user import User, UserCreated


class UserController(Database):
    """Контроллер для работы с таблицей users"""

    async def insert(
        self,
        data: UserCreated,
        _session: AsyncSession | None = None,
    ) -> UUID:
        """Добавить нового пользователя в БД"""
        user_uuid = uuid.uuid4()
        data = {"uuid": user_uuid, "name": data.name, "password": data.password}
        _sql = text(
            """
            INSERT INTO users ( uuid,  name,  password)
                 VALUES       (:uuid, :name, :password)
            """
        )
        async with self.session(_session) as session:
            await session.execute(_sql, data)
        return user_uuid

    async def get_user(
        self,
        uuid: UUID | None = None,
        login: str | None = None,
        _is_login: bool = False,
        _session: AsyncSession | None = None,
    ) -> User:
        """Получить данные конкретного пользователя

        Поиск пользователя осуществляется по одному из уникальных параметру.
        Если указаны оба, то uuid - будет в приоритете.

        Args:
            uuid (UUID | None, optional): UUID пользователя. Defaults to None.
            login (str | None, optional): Уникальный логин пользователя. Defaults to None.

        Returns:
            User: Объект данных пользователья
        """
        if uuid:
            find_param = "uuid"
            value = uuid
        else:
            find_param = "name"
            value = login

        _sql = text(
            f"""
            SELECT u.uuid,
                   u.name, 
                   u.password
              FROM users u
            WHERE {find_param} = '{value}'
            """
        )
        async with self.session(_session) as session:
            _raw_res = await session.execute(_sql)
            _res = _raw_res.fetchall()
            if len(_res) > 1:
                # TODO сделать нормальные ошибки
                raise ValueError("Get more than one user")
            _res = _res[0]
            if _is_login:
                return User(uuid=_res[0], name=_res[1], password=_res[2])
            return User(uuid=_res[0], name=_res[1])
