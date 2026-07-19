"""Название: ruleset.py

Путь: backend/db/controller/ruleset.py
Автор: stepapetruk@ya.ru
Дата: [31.05.2026]::2026-May-Sunday
Описание:

Контроллер для работы с книгами правил.

Содержит методы создания, получения, частичного обновления и удаления
книг правил из таблицы rulesets.
"""

import datetime
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.base import Database
from backend.db.model.ruleset import Ruleset, RulesetCreated, RulesetUpdated
from backend.models.ruleset import Status


class RulesetController(Database):
    """Контроллер для работы с таблицей rulesets.

    Инкапсулирует SQL-запросы, связанные с книгами правил:
    создание, получение, частичное обновление и удаление записей.
    """

    async def insert(
        self,
        data: RulesetCreated,
        _session: AsyncSession | None = None,
    ) -> UUID:
        """Добавить новую книгу правил в таблицу rulesets.

        Создаёт UUID новой книги правил и выполняет INSERT-запрос.

        Время создания и обновления проставляется на стороне приложения
        в UTC.

        Args:
            data: Данные создаваемой книги правил.
            _session: Внешняя асинхронная SQLAlchemy-сессия.
                Если не передана, контроллер создаёт сессию самостоятельно.

        Returns:
            UUID созданной книги правил.
        """
        sql = text(
            """
            INSERT INTO rulesets (
                uuid,
                owner_uuid,
                parent_uuid,
                name,
                description,
                version,
                status,
                is_public,
                created_at,
                updated_at
            )
            VALUES (
                :uuid,
                :owner_uuid,
                :parent_uuid,
                :name,
                :description,
                :version,
                :status,
                :is_public,
                :created_at,
                :updated_at
            )
            RETURNING uuid
            """
        )

        ruleset_uuid = uuid.uuid4()
        now = datetime.datetime.now(tz=datetime.UTC)

        params = {
            "uuid": ruleset_uuid,
            "owner_uuid": data.owner_uuid,
            "parent_uuid": data.parent_uuid,
            "name": data.name,
            "description": data.description,
            "version": data.version,
            "status": data.status.value,
            "is_public": data.is_public,
            "created_at": now,
            "updated_at": now,
        }

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            inserted_uuid = result.scalar_one()

        return inserted_uuid

    async def get(
        self,
        ruleset_uuid: UUID,
        _session: AsyncSession | None = None,
        owner_uuid: UUID | None = None,
        include_public: bool = False,
    ) -> Ruleset | None:
        """Получить книгу правил по UUID.

        Args:
            ruleset_uuid: UUID книги правил.
            _session: Внешняя асинхронная SQLAlchemy-сессия.
                Если не передана, контроллер создаёт сессию самостоятельно.
            owner_uuid: UUID владельца, используемый как фильтр доступа.
            include_public: Разрешить публичные книги вместе с книгами
                указанного владельца.

        Returns:
            Книга правил, если запись найдена. Иначе None.
        """
        access_filter = ""
        params: dict[str, Any] = {"uuid": ruleset_uuid}

        if owner_uuid is not None:
            params["owner_uuid"] = owner_uuid
            if include_public:
                access_filter = " AND (owner_uuid = :owner_uuid OR is_public IS TRUE)"
            else:
                access_filter = " AND owner_uuid = :owner_uuid"

        sql = text(
            """
            SELECT
                uuid,
                owner_uuid,
                parent_uuid,
                name,
                description,
                version,
                status,
                is_public,
                created_at,
                updated_at
            FROM rulesets
            WHERE uuid = :uuid
            """
            + access_filter
        )

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            row = result.mappings().one_or_none()

        if row is None:
            return None

        return Ruleset(
            uuid=row["uuid"],
            owner_uuid=row["owner_uuid"],
            parent_uuid=row["parent_uuid"],
            name=row["name"],
            description=row["description"],
            version=row["version"],
            status=Status(row["status"]),
            is_public=row["is_public"],
            created_at=self.parse_datetime(row["created_at"]),
            updated_at=self.parse_datetime(row["updated_at"]),
        )

    async def update(
        self,
        data: RulesetUpdated,
        _session: AsyncSession | None = None,
        owner_uuid: UUID | None = None,
    ) -> UUID:
        """Частично обновить книгу правил.

        В UPDATE-запрос попадают только поля, которые были переданы
        пользователем явно.

        Поля owner_uuid и parent_uuid допускают явную передачу None,
        чтобы отвязать книгу правил от владельца или родительской записи.

        Args:
            data: Данные для частичного обновления книги правил.
            _session: Внешняя асинхронная SQLAlchemy-сессия.
                Если не передана, контроллер создаёт сессию самостоятельно.
            owner_uuid: UUID владельца для атомарной проверки прав в UPDATE.

        Returns:
            UUID обновлённой книги правил.

        Raises:
            ValueError: Если не передано ни одного поля для обновления,
                передано неизвестное поле или запись не найдена.
        """
        allowed_fields = {
            "owner_uuid",
            "parent_uuid",
            "name",
            "description",
            "version",
            "status",
            "is_public",
        }

        nullable_fields = {
            "owner_uuid",
            "parent_uuid",
        }

        fields_to_update = data.model_fields_set - {"uuid"}

        if not fields_to_update:
            raise ValueError("Не были переданы данные для обновления книги правил!")

        if "parent_uuid" in fields_to_update and data.parent_uuid == data.uuid:
            raise ValueError("Книга правил не может быть своим собственным родителем")

        details: list[str] = []
        params: dict[str, Any] = {
            "uuid": data.uuid,
            "updated_at": datetime.datetime.now(tz=datetime.UTC),
        }

        for field_name in sorted(fields_to_update):
            if field_name not in allowed_fields:
                raise ValueError(f"Поле {field_name!r} нельзя обновлять")

            value = getattr(data, field_name)

            if value is None and field_name not in nullable_fields:
                raise ValueError(f"Поле {field_name!r} не может быть пустым")

            if isinstance(value, Status):
                value = value.value

            bind_name = f"update_{field_name}"
            details.append(f"{field_name} = :{bind_name}")
            params[bind_name] = value

        details.append("updated_at = :updated_at")

        owner_filter = ""
        if owner_uuid is not None:
            owner_filter = " AND owner_uuid = :access_owner_uuid"
            params["access_owner_uuid"] = owner_uuid

        sql = text(
            f"""
            UPDATE rulesets
            SET {", ".join(details)}
            WHERE uuid = :uuid
            {owner_filter}
            RETURNING uuid
            """
        )

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            updated_uuid = result.scalar_one_or_none()

        if updated_uuid is None:
            raise ValueError(f"Книга правил с UUID {data.uuid} не найдена или не принадлежит пользователю")

        return updated_uuid

    async def delete(
        self,
        ruleset_uuid: UUID,
        _session: AsyncSession | None = None,
        owner_uuid: UUID | None = None,
    ) -> None:
        """Удалить книгу правил из таблицы rulesets.

        Выполняет физическое удаление записи по UUID книги правил.

        Args:
            ruleset_uuid: UUID удаляемой книги правил.
            _session: Внешняя асинхронная SQLAlchemy-сессия.
                Если не передана, контроллер создаёт сессию самостоятельно.
            owner_uuid: UUID владельца для атомарной проверки прав в DELETE.

        Raises:
            ValueError: Если книга правил не найдена.
        """
        owner_filter = ""
        params: dict[str, Any] = {"uuid": ruleset_uuid}

        if owner_uuid is not None:
            owner_filter = " AND owner_uuid = :owner_uuid"
            params["owner_uuid"] = owner_uuid

        sql = text(
            """
            DELETE FROM rulesets
            WHERE uuid = :uuid
            """
            + owner_filter
            + " RETURNING uuid"
        )

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            deleted_uuid = result.scalar_one_or_none()

        if deleted_uuid is None:
            raise ValueError(f"Книга правил с UUID {ruleset_uuid} не найдена или не принадлежит пользователю")
