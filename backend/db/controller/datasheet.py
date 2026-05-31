"""Название: datasheet.py

Путь: backend/db/controller/datasheet.py
Автор: stepapetruk@ya.ru
Дата: [07.05.2026]::2026-May-Thursday
Описание:

Контроллер для работы с листами персонажей.

Содержит методы создания, получения, обновления и удаления листов персонажей
из таблицы datasheets.
"""

import datetime
import json
import uuid
from uuid import UUID

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.base import Database
from backend.db.model.datasheet import Datasheet, DatasheetCreated, DatasheetUpdated
from backend.models.datasheet import Features, Inventory, Stats, Wallet


class DatasheetController(Database):
    """Контроллер для работы с таблицей datasheets.

    Инкапсулирует SQL-запросы, связанные с листами персонажей:
    создание, получение, частичное обновление и удаление записей.

    JSONB-поля листа персонажа сериализуются через Pydantic-модели и передаются
    в PostgreSQL с явным указанием типа JSONB.
    """

    async def insert(
        self,
        data: DatasheetCreated,
        _session: AsyncSession | None = None,
    ) -> UUID:
        """Добавить новый лист персонажа в таблицу datasheets.

        Создаёт UUID нового листа персонажа, подготавливает JSONB-поля
        `wallet`, `inventory`, `stats` и `features`, после чего выполняет
        INSERT-запрос.

        Время создания и обновления проставляется на стороне приложения
        в UTC.

        Args:
            data (DatasheetCreated): Данные создаваемого листа персонажа.
                Содержит UUID владельца, имя персонажа и вложенные модели
                кошелька, инвентаря, характеристик и черт.
            _session (AsyncSession | None, optional): Внешняя асинхронная
                SQLAlchemy-сессия. Если передана, используется она. Если не
                передана, контроллер создаёт сессию самостоятельно.
                Defaults to None.

        Returns:
            UUID: UUID созданного листа персонажа.
        """
        # TODO добавить потом рассу
        _sql = text(
            """
                INSERT INTO datasheets (
                                uuid,
                                user_uuid,
                                name,
                                wallet,
                                inventory,
                                stats,
                                features,
                                created_at,
                                updated_at
                            )
                     VALUES            (
                                :uuid,
                                :user_uuid,
                                :name, 
                                :wallet, 
                                :inventory, 
                                :stats, 
                                :features, 
                                :created_at, 
                                :updated_at
                            )
            """
        ).bindparams(
            bindparam("wallet", type_=JSONB),
            bindparam("inventory", type_=JSONB),
            bindparam("stats", type_=JSONB),
            bindparam("features", type_=JSONB),
        )
        sheet_uuid = uuid.uuid4()
        now = datetime.datetime.now(tz=datetime.UTC)
        _params = {
            "uuid": sheet_uuid,
            "user_uuid": data.user_uuid,
            "name": data.name,
            "wallet": data.wallet.as_dict(),
            "inventory": data.inventory.as_dict(),
            "stats": data.stats.as_dict(),
            "features": data.features.as_dict(),
            "created_at": now,
            "updated_at": now,
        }
        async with self.session(_session) as session:
            await session.execute(_sql, _params)
        return sheet_uuid

    async def get(
        self,
        sheet_uuid: UUID,
        _session: AsyncSession | None = None,
    ) -> Datasheet | None:
        """Получить лист персонажа по UUID.

        Выполняет SELECT-запрос к таблице datasheets и собирает результат
        в Pydantic-модель `Datasheet`.

        JSONB-поля из БД приводятся к соответствующим вложенным моделям:
        `Wallet`, `Inventory`, `Stats` и `Features`.

        Args:
            sheet_uuid (UUID): UUID листа персонажа, который нужно получить.
            _session (AsyncSession | None, optional): Внешняя асинхронная
                SQLAlchemy-сессия. Если передана, используется она. Если не
                передана, контроллер создаёт сессию самостоятельно.
                Defaults to None.

        Returns:
            Datasheet | None: Лист персонажа, если запись найдена.
            Если запись не найдена, возвращается None.

        Raises:
            ValueError: Возникает, если по одному UUID найдено больше одного
                листа персонажа.
        """
        _sql = text(
            """
                SELECT (
                        uuid,       -- 0
                        user_uuid,  -- 1
                        name,       -- 2
                        wallet,     -- 3
                        inventory,  -- 4
                        stats,      -- 5
                        features,   -- 6
                        created_at, -- 7
                        updated_at  -- 8
                )
                  FROM datasheets
                  WHERE uuid = :uuid
            """
        )

        async with self.session(_session) as session:
            row = await session.execute(_sql, {"uuid": sheet_uuid})
            rows = row.fetchall()
            if len(rows) > 1:
                raise ValueError("Get more than one datasheet")
            if row is None or row == []:
                return None
        res = rows[0]
        return Datasheet(
            uuid=res[0],
            user_uuid=res[1],
            name=res[2],
            wallet=Wallet(**json.loads(res[3])),
            inventory=Inventory(**json.loads(res[4])),
            stats=Stats(**json.loads(res[5])),
            features=Features(**json.loads(res[6])),
            created_at=self.parse_datetime(res[7]),
            updated_at=self.parse_datetime(res[8]),
            race=None,
        )

    async def update(
        self,
        data: DatasheetUpdated,
        _session: AsyncSession | None = None,
    ) -> UUID:
        """Обновить лист персонажа.

        Выполняет частичное обновление листа персонажа. В UPDATE-запрос
        попадают только те поля, которые были переданы в модели
        `DatasheetUpdated`.

        JSONB-поля передаются в PostgreSQL с явным указанием типа JSONB, чтобы
        SQLAlchemy/psycopg корректно сериализовали словари Python.

        Args:
            data (DatasheetUpdated): Данные для обновления листа персонажа.
                Поле `uuid` обязательно, остальные поля обновляются только при
                наличии значения.
            _session (AsyncSession | None, optional): Внешняя асинхронная
                SQLAlchemy-сессия. Если передана, используется она. Если не
                передана, контроллер создаёт сессию самостоятельно.
                Defaults to None.

        Returns:
            UUID: UUID обновлённого листа персонажа.

        Raises:
            ValueError: Возникает, если не передано ни одного поля для
                обновления.
        """
        now = datetime.datetime.now(tz=datetime.UTC)

        params = {
            "updated_at": now,
            "uuid": data.uuid,
        }

        details: list[str] = []
        jsonb_fields: list[str] = []

        if data.wallet is not None:
            details.append("wallet = :wallet")
            params["wallet"] = data.wallet.as_dict()
            jsonb_fields.append("wallet")

        if data.stats is not None:
            details.append("stats = :stats")
            params["stats"] = data.stats.as_dict()
            jsonb_fields.append("stats")

        if data.inventory is not None:
            details.append("inventory = :inventory")
            params["inventory"] = data.inventory.as_dict()
            jsonb_fields.append("inventory")

        if data.features is not None:
            details.append("features = :features")
            params["features"] = data.features.as_dict()
            jsonb_fields.append("features")

        if data.name is not None:
            details.append("name = :name")
            params["name"] = data.name

        if len(details) == 0:
            # TODO сделать нормальные ошибки
            raise ValueError("Не были переданы данные для обновления листа персонажа!")

        details.append("updated_at = :updated_at")

        sql = text(
            f"""
            UPDATE datasheets AS ds
            SET {", ".join(details)}
            WHERE ds.uuid = :uuid
            """
        )

        bind_params = [bindparam(field_name, type_=JSONB) for field_name in jsonb_fields]

        if bind_params:
            sql = sql.bindparams(*bind_params)

        async with self.session(_session) as session:
            await session.execute(sql, params)

        return data.uuid

    async def delete(
        self,
        sheet_uuid: UUID,
        _session: AsyncSession | None = None,
    ) -> None:
        """Удалить лист персонажа из таблицы datasheets.

        Выполняет физическое удаление записи по UUID листа персонажа.

        Args:
            sheet_uuid (UUID): UUID листа персонажа, который нужно удалить.
            _session (AsyncSession | None, optional): Внешняя асинхронная
                SQLAlchemy-сессия. Если передана, используется она. Если не
                передана, контроллер создаёт сессию самостоятельно.
                Defaults to None.

        Returns:
            None: Метод ничего не возвращает.
        """
        _sql = text(
            """
                DELETE FROM datasheets
                 WHERE uuid = :uuid
            """
        )

        async with self.session(_session) as session:
            await session.execute(_sql, {"uuid": sheet_uuid})
