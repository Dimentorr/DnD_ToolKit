"""Название: user.py

Путь: backend/db/controller/user.py
Автор: stepapetruk@ya.ru
Дата: [04.05.2026]::2026-May-Monday
Описание:

Контроллер для работы с пользователями.

Содержит методы создания пользователя и получения пользовательских данных
из таблицы users.
"""

import datetime
import uuid
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.base import Database
from backend.db.model.user import User, UserCreated


class UserController(Database):
    """Контроллер для работы с таблицей users.

    Инкапсулирует SQL-запросы, связанные с пользователями:
    создание новой записи и получение пользователя по UUID или логину.

    Используется как часть слоя доступа к данным.
    """

    async def insert(
        self,
        data: UserCreated,
        _session: AsyncSession | None = None,
    ) -> UUID:
        """Добавить нового пользователя в таблицу users.

        Создаёт UUID нового пользователя, подготавливает параметры запроса и
        выполняет INSERT в таблицу users.

        Пароль в `data.password` должен быть заранее захеширован на уровне
        auth-сервиса или router'а. Метод не выполняет хеширование пароля
        самостоятельно.

        Если внешняя сессия не передана, метод создаёт собственную сессию через
        контекстный менеджер базового контроллера.

        Args:
            data (UserCreated): Данные создаваемого пользователя. Содержит имя
                пользователя, email и заранее подготовленный хеш пароля.
            _session (AsyncSession | None, optional): Внешняя асинхронная
                SQLAlchemy-сессия. Если передана, используется она. Если не
                передана, контроллер создаёт сессию самостоятельно.
                Defaults to None.

        Returns:
            UUID: UUID созданного пользователя.
        """
        user_uuid = uuid.uuid4()
        data = {
            "uuid": user_uuid,
            "name": data.name,
            "email": data.email,
            "password": data.password,
            "created_at": datetime.datetime.now(tz=datetime.UTC),
            "updated_at": datetime.datetime.now(tz=datetime.UTC),
        }
        _sql = text(
            """
            INSERT INTO users ( uuid,  name,  password,  email,  created_at,  updated_at)
                 VALUES       (:uuid, :name, :password, :email, :created_at, :updated_at)
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
    ) -> User | None:
        """Получить пользователя из таблицы users.

        Выполняет поиск пользователя по одному из уникальных параметров:
        UUID или логину. Если одновременно переданы UUID и логин, приоритет
        отдаётся UUID.

        По умолчанию возвращает пользовательские данные без пароля. Если
        `_is_login=True`, дополнительно заполняет поле `password` хешем пароля
        из БД. Этот режим нужен для авторизации, когда пароль из формы нужно
        проверить через `verify_password`.

        Args:
            uuid (UUID | None, optional): UUID пользователя. Имеет приоритет
                над `login`, если оба параметра переданы.
                Defaults to None.
            login (str | None, optional): Уникальный логин пользователя.
                Используется для поиска, если `uuid` не передан.
                Defaults to None.
            _is_login (bool, optional): Признак режима авторизации. Если True,
                возвращаемая модель содержит хеш пароля. Если False, пароль
                не добавляется в модель.
                Defaults to False.
            _session (AsyncSession | None, optional): Внешняя асинхронная
                SQLAlchemy-сессия. Если передана, используется она. Если не
                передана, контроллер создаёт сессию самостоятельно.
                Defaults to None.

        Returns:
            User | None: Данные пользователя, если запись найдена.
            Если пользователь не найден, возвращается None.

        Raises:
            ValueError: Возникает, если не передан ни `uuid`, ни `login`,
                либо если запрос вернул больше одного пользователя.
        """
        if uuid is not None:
            find_param = "uuid"
            params = {"value": uuid}
        elif login is not None:
            find_param = "name"
            params = {"value": login}
        else:
            raise ValueError("Не были переданы параметры для поиска")
        _sql = text(
            f"""
            SELECT u.uuid,          -- 0
                   u.name,          -- 1
                   u.email,         -- 2
                   u.created_at,    -- 3
                   u.updated_at,    -- 4
                   u.password       -- 5
              FROM users u
             WHERE u.{find_param} = :value
            """
        )
        async with self.session(_session) as session:
            _raw_res = await session.execute(_sql, params)
            _res = _raw_res.fetchall()
            if len(_res) > 1:
                # TODO сделать нормальные ошибки
                raise ValueError("Get more than one user")
            if len(_res) == 0:
                return None
            _res = _res[0]
            if _is_login:
                return User(
                    uuid=_res[0],
                    name=_res[1],
                    email=_res[2],
                    created_at=_res[3],
                    updated_at=_res[4],
                    password=_res[5],
                )
            return User(
                uuid=_res[0],
                name=_res[1],
                email=_res[2],
                created_at=_res[3],
                updated_at=_res[4],
            )
