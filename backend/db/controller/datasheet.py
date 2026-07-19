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
import uuid
from typing import Any
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
        sql = text(
            """
            WITH context AS (
                SELECT
                    rulesets.uuid AS ruleset_uuid,
                    (
                        :race_uuid IS NULL
                        OR EXISTS (
                            SELECT 1
                            FROM races
                            WHERE races.uuid = :race_uuid
                              AND races.ruleset_uuid = rulesets.uuid
                        )
                    ) AS race_valid
                FROM rulesets
                WHERE rulesets.uuid = :ruleset_uuid
                  AND (rulesets.owner_uuid = :user_uuid OR rulesets.is_public IS TRUE)
            ),
            inserted AS (
                INSERT INTO datasheets (
                    uuid,
                    user_uuid,
                    ruleset_uuid,
                    name,
                    race_uuid,
                    wallet,
                    inventory,
                    stats,
                    features,
                    created_at,
                    updated_at
                )
                SELECT
                    :uuid,
                    :user_uuid,
                    context.ruleset_uuid,
                    :name,
                    :race_uuid,
                    :wallet,
                    :inventory,
                    :stats,
                    :features,
                    :created_at,
                    :updated_at
                FROM context
                WHERE context.race_valid
                RETURNING uuid
            )
            SELECT
                EXISTS (SELECT 1 FROM context) AS ruleset_found,
                COALESCE((SELECT race_valid FROM context), FALSE) AS race_valid,
                (SELECT uuid FROM inserted) AS inserted_uuid
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
            "ruleset_uuid": data.ruleset_uuid,
            "name": data.name,
            "race_uuid": data.race,
            "wallet": data.wallet.as_dict(),
            "inventory": data.inventory.as_dict(),
            "stats": data.stats.as_dict(),
            "features": data.features.as_dict(),
            "created_at": now,
            "updated_at": now,
        }
        async with self.session(_session) as session:
            result = await session.execute(sql, _params)
            row = result.mappings().one()

        if not row["ruleset_found"]:
            raise ValueError("Книга правил не найдена или недоступна")
        if not row["race_valid"]:
            raise ValueError("Раса не найдена в выбранной книге правил")
        if row["inserted_uuid"] is None:
            raise RuntimeError("При создании листа персонажа БД не вернула UUID")

        return row["inserted_uuid"]

    async def get(
        self,
        sheet_uuid: UUID,
        _session: AsyncSession | None = None,
        owner_uuid: UUID | None = None,
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
            owner_uuid (UUID | None, optional): Ограничить операцию листом
                указанного владельца. Defaults to None.

        Returns:
            Datasheet | None: Лист персонажа, если запись найдена.
            Если запись не найдена, возвращается None.

        Raises:
            ValueError: Возникает, если по одному UUID найдено больше одного
                листа персонажа.
        """
        owner_filter = ""
        params: dict[str, Any] = {"uuid": sheet_uuid}

        if owner_uuid is not None:
            owner_filter = " AND user_uuid = :owner_uuid"
            params["owner_uuid"] = owner_uuid

        sql = text(
            """
                SELECT uuid,
                       user_uuid,
                       ruleset_uuid,
                       race_uuid,
                       name,
                       wallet,
                       inventory,
                       stats,
                       features,
                       created_at,
                       updated_at
                FROM datasheets
                WHERE uuid = :uuid
            """
            + owner_filter
        )

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            row = result.mappings().one_or_none()

        if row is None:
            return None

        return Datasheet(
            uuid=row["uuid"],
            user_uuid=row["user_uuid"],
            ruleset_uuid=row["ruleset_uuid"],
            race=row["race_uuid"],
            name=row["name"],
            wallet=Wallet.model_validate(row["wallet"]),
            inventory=Inventory.model_validate(row["inventory"]),
            stats=Stats.model_validate(row["stats"]),
            features=Features.model_validate(row["features"]),
            created_at=self.parse_datetime(row["created_at"]),
            updated_at=self.parse_datetime(row["updated_at"]),
        )

    async def update(
        self,
        data: DatasheetUpdated,
        _session: AsyncSession | None = None,
        owner_uuid: UUID | None = None,
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
            owner_uuid (UUID | None, optional): UUID владельца для атомарной
                проверки прав в UPDATE. Defaults to None.

        Returns:
            UUID: UUID обновлённого листа персонажа.

        Raises:
            ValueError: Возникает, если не передано ни одного поля для
                обновления.
        """
        now = datetime.datetime.now(tz=datetime.UTC)

        params: dict[str, Any] = {
            "updated_at": now,
            "uuid": data.uuid,
            "ruleset_uuid": data.ruleset_uuid,
            "race_uuid": data.race,
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

        if "ruleset_uuid" in data.model_fields_set:
            if data.ruleset_uuid is None:
                raise ValueError("Поле ruleset_uuid не может быть null")
            details.append("ruleset_uuid = :ruleset_uuid")
            params["ruleset_uuid"] = data.ruleset_uuid

        if "race" in data.model_fields_set:
            details.append("race_uuid = :race_uuid")
            params["race_uuid"] = data.race

        if len(details) == 0:
            # TODO сделать нормальные ошибки
            raise ValueError("Не были переданы данные для обновления листа персонажа!")

        details.append("updated_at = :updated_at")

        change_ruleset = "ruleset_uuid" in data.model_fields_set
        change_race = "race" in data.model_fields_set
        params["change_ruleset"] = change_ruleset
        params["change_race"] = change_race
        params["validate_relations"] = change_ruleset or change_race

        owner_filter = ""
        ruleset_access_filter = ""
        if owner_uuid is not None:
            owner_filter = " AND ds.user_uuid = :owner_uuid"
            ruleset_access_filter = " AND (rulesets.owner_uuid = :owner_uuid OR rulesets.is_public IS TRUE)"
            params["owner_uuid"] = owner_uuid

        relation_filter = (
            """
            AND (
                NOT :validate_relations
                OR EXISTS (
                    SELECT 1
                    FROM rulesets
                    WHERE rulesets.uuid = (
                        CASE WHEN :change_ruleset THEN :ruleset_uuid ELSE ds.ruleset_uuid END
                    )
            """
            + ruleset_access_filter
            + """
                    AND (
                        (CASE WHEN :change_race THEN :race_uuid ELSE ds.race_uuid END) IS NULL
                        OR EXISTS (
                            SELECT 1
                            FROM races
                            WHERE races.uuid = (
                                CASE WHEN :change_race THEN :race_uuid ELSE ds.race_uuid END
                            )
                              AND races.ruleset_uuid = rulesets.uuid
                        )
                    )
                )
            )
            """
        )

        sql = text(
            f"""
            UPDATE datasheets AS ds
            SET {", ".join(details)}
            WHERE ds.uuid = :uuid
            {owner_filter}
            {relation_filter}
            RETURNING ds.uuid
            """
        )

        bind_params = [bindparam(field_name, type_=JSONB) for field_name in jsonb_fields]

        if bind_params:
            sql = sql.bindparams(*bind_params)

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            updated_uuid = result.scalar_one_or_none()

        if updated_uuid is None:
            raise ValueError(f"Лист персонажа с UUID {data.uuid} не найден или не принадлежит пользователю")

        return updated_uuid

    async def delete(
        self,
        sheet_uuid: UUID,
        _session: AsyncSession | None = None,
        owner_uuid: UUID | None = None,
    ) -> None:
        """Удалить лист персонажа из таблицы datasheets.

        Выполняет физическое удаление записи по UUID листа персонажа.

        Args:
            sheet_uuid (UUID): UUID листа персонажа, который нужно удалить.
            _session (AsyncSession | None, optional): Внешняя асинхронная
                SQLAlchemy-сессия. Если передана, используется она. Если не
                передана, контроллер создаёт сессию самостоятельно.
                Defaults to None.
            owner_uuid (UUID | None, optional): UUID владельца для атомарной
                проверки прав в DELETE. Defaults to None.

        Returns:
            None: Метод ничего не возвращает.
        """
        owner_filter = ""
        params: dict[str, Any] = {"uuid": sheet_uuid}

        if owner_uuid is not None:
            owner_filter = " AND user_uuid = :owner_uuid"
            params["owner_uuid"] = owner_uuid

        sql = text(
            """
                DELETE FROM datasheets
                WHERE uuid = :uuid
            """
            + owner_filter
            + " RETURNING uuid"
        )

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            deleted_uuid = result.scalar_one_or_none()

        if deleted_uuid is None:
            raise ValueError(f"Лист персонажа с UUID {sheet_uuid} не найден или не принадлежит пользователю")
