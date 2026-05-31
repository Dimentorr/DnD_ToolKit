"""Название: token.py

Путь: backend/db/controller/token.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Контроллер для работы с токенами.
"""

import datetime
import uuid
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.base import Database
from backend.db.model.token import TokenCreated, TokenData
from core import security
from core.config import settings


class TokenController(Database):
    """Добавить refresh-токен в таблицу tokens.

    Сохраняет refresh-токен в БД в виде детерминированного HMAC-SHA256 хеша.
    Сырой refresh-токен в БД не сохраняется.

    Args:
        data (TokenCreated): Данные создаваемого refresh-токена. Поле `token`
            должно содержать сырой refresh-токен, а не его хеш.
        _session (AsyncSession | None, optional): Внешняя асинхронная
            SQLAlchemy-сессия. Если передана, используется она. Если не
            передана, контроллер создаёт сессию самостоятельно.
            Defaults to None.

    Returns:
        UUID: UUID созданной записи refresh-токена.
    """

    async def insert(
        self,
        data: TokenCreated,
        _session: AsyncSession | None = None,
    ) -> UUID:
        """Добавить нового пользователя в БД"""
        token_uuid = uuid.uuid4()
        exp = datetime.timedelta(days=settings.app.REFRESH_TOKEN_EXPIRE_DAYS)
        data = {
            "uuid": token_uuid,
            "user_uuid": data.user_uuid,
            "token": await security.get_hash(data.token, is_static=True),
            "expires_at": datetime.datetime.now(tz=datetime.UTC) + exp,
            "created_at": datetime.datetime.now(tz=datetime.UTC),
            "updated_at": datetime.datetime.now(tz=datetime.UTC),
        }
        _sql = text(
            """
            INSERT INTO tokens ( uuid,  user_uuid,  token,  expires_at,  created_at,  updated_at)
                 VALUES        (:uuid, :user_uuid, :token, :expires_at, :created_at, :updated_at)
            """
        )
        async with self.session(_session) as session:
            await session.execute(_sql, data)
        return token_uuid

    async def get_user_token(
        self,
        user_uuid: UUID,
        _session: AsyncSession | None = None,
    ) -> TokenData | None:
        """Получить единственный refresh-токен пользователя.

        Важно: метод подходит только для схемы, где у пользователя может быть
        максимум один активный refresh-токен. Для refresh-token rotation лучше
        использовать `get_by_token_hash`.
        """

        data = {"user_uuid": user_uuid}

        _sql = text(
            """
        SELECT uuid, 
               user_uuid,
               token,
               expires_at,
               created_at,
               updated_at
          FROM tokens
          WHERE user_uuid = :user_uuid
        """
        )
        async with self.session(_session) as session:
            row = await session.execute(_sql, data)
            rows = row.fetchall()
            if len(rows) > 1:
                raise ValueError("Get more than one token")
            if row is None or row == []:
                return None
        res = rows[0]
        return TokenData(
            uuid=res[0],
            user_uuid=res[1],
            token=res[2],
            expires_at=res[3],
            revoked_at=res[4],
            created_at=res[5],
            updated_at=res[6],
        )

    async def get_by_token_hash(
        self,
        token_hash: str,
        _session: AsyncSession | None = None,
    ) -> TokenData | None:
        """Получить refresh-токен по его хешу.

        Выполняет поиск записи в таблице tokens по значению хеша токена.
        Метод используется при обновлении пары токенов: сырой refresh-токен
        сначала хешируется, после чего по полученному хешу ищется запись в БД.

        Args:
            token_hash (str): Хеш refresh-токена.
            _session (AsyncSession | None, optional): Внешняя асинхронная
                SQLAlchemy-сессия. Если передана, используется она. Если не
                передана, контроллер создаёт сессию самостоятельно.
                Defaults to None.

        Returns:
            TokenData | None: Данные токена, если запись найдена.
            Если токен не найден, возвращается None.

        Raises:
            ValueError: Возникает, если по одному хешу найдено больше одной записи.
                Такая ситуация считается нарушением уникальности данных.
        """
        params = {"token_hash": token_hash}

        _sql = text(
            """
            SELECT uuid,      -- 0
                user_uuid,    -- 1
                token,        -- 2
                expires_at,   -- 3
                revoked_at,   -- 4
                created_at,   -- 5
                updated_at    -- 6
            FROM tokens
            WHERE token = :token_hash
            """
        )

        async with self.session(_session) as session:
            result = await session.execute(_sql, params)
            rows = result.fetchall()

        if len(rows) > 1:
            raise ValueError("Get more than one token by token hash")

        if not rows:
            return None

        row = rows[0]

        return TokenData(
            uuid=row[0],
            user_uuid=row[1],
            token=row[2],
            expires_at=row[3],
            revoked_at=row[4],
            created_at=row[5],
            updated_at=row[6],
        )

    async def revoke(
        self,
        token_uuid: UUID,
        _session: AsyncSession | None = None,
    ) -> None:
        """Отозвать refresh-токен.

        Проставляет значение revoked_at для записи в таблице tokens.
        После отзыва токен считается недействительным и не должен использоваться
        для получения новой пары access/refresh-токенов.

        Метод не удаляет запись из БД, чтобы сохранить историю сессии и иметь
        возможность анализировать повторное использование уже отозванного токена.

        Args:
            token_uuid (UUID): UUID отзываемого токена.
            _session (AsyncSession | None, optional): Внешняя асинхронная
                SQLAlchemy-сессия. Если передана, используется она. Если не
                передана, контроллер создаёт сессию самостоятельно.
                Defaults to None.

        Returns:
            None: Метод ничего не возвращает.
        """
        now = datetime.datetime.now(tz=datetime.UTC)

        params = {
            "uuid": token_uuid,
            "revoked_at": now,
            "updated_at": now,
        }

        _sql = text(
            """
            UPDATE tokens
            SET revoked_at = :revoked_at,
                updated_at = :updated_at
            WHERE uuid = :uuid
            AND revoked_at IS NULL
            """
        )

        async with self.session(_session) as session:
            await session.execute(_sql, params)

    async def refresh_tokens(
        self,
        refresh_token: str | None,
    ) -> tuple[str, str]:
        """Обновить пару access/refresh-токенов.

        Проверяет refresh-токен, ищет его хеш в БД, проверяет срок действия и
        признак отзыва. После успешной проверки отзывает старый refresh-токен,
        создаёт новую пару токенов и сохраняет новый refresh-токен в БД.

        Args:
            refresh_token (str | None): Сырой refresh-токен пользователя из cookie.

        Returns:
            tuple[str, str]: Новая пара `(access_token, refresh_token)`.

        Raises:
            ValueError: Возникает, если refresh-токен отсутствует, невалиден,
                отозван, истёк или не найден в БД.
        """
        if refresh_token is None:
            raise ValueError("Refresh token is missing")

        payload = await security.decode_token(refresh_token)

        if payload is None:
            raise ValueError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_uuid = payload.get("sub")

        if user_uuid is None:
            raise ValueError("Invalid refresh token payload")

        db_token = await self.get_by_token_hash(token_hash=await security.get_hash(is_static=True, obj=refresh_token))

        if db_token is None:
            raise ValueError("Refresh token not found")

        now = datetime.datetime.now(datetime.UTC)

        if db_token.revoked_at is not None:
            raise ValueError("Refresh token rewoked")

        if db_token.expires_at <= now:
            raise ValueError("Refresh token expired")
        new_access_token, new_refresh_token = await security.refresh_tokens(
            refresh_token=refresh_token,
        )

        async with self.session() as session:
            exp = datetime.timedelta(days=settings.app.REFRESH_TOKEN_EXPIRE_DAYS)
            await self.revoke(
                token_uuid=db_token.uuid,
                _session=session,
            )
            await self.insert(
                data=TokenCreated(
                    user_uuid=UUID(user_uuid),
                    token=new_refresh_token,
                    expires_at=datetime.datetime.now(datetime.UTC) + exp,
                ),
                _session=session,
            )

        return new_access_token, new_refresh_token
