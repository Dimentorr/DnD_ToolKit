"""Название: race.py

Путь: backend/db/controller/race.py
Автор: stepapetruk@ya.ru
Дата: [19.07.2026]::2026-July-Sunday
Описание:

Контроллер для работы с расами персонажей.

Содержит методы создания, получения, постраничного получения, частичного
обновления и удаления рас персонажей из таблицы `races`.

Доступ к расам проверяется через связанную книгу правил `rulesets`.
Пользователь может изменять только те расы, которые относятся к принадлежащим
ему книгам правил. Для операций чтения контроллер дополнительно может учитывать
публичные книги правил через параметр `include_public`.

Контроллер также проверяет доменные ограничения иерархии рас:
родительская раса должна принадлежать той же книге правил, а при обновлении
родителя нельзя создать циклическую зависимость внутри дерева рас.
"""

import datetime
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import UUID as SqlUUID
from sqlalchemy import bindparam, text
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.base import Database
from backend.db.model.race import Race, RaceCreated, RaceUpdated


class RaceNotFoundError(LookupError):
    """Ошибка отсутствия доступной расы или книги правил.

    Используется, когда запрошенная раса или связанная книга правил
    не существует либо недоступна текущему пользователю с учётом переданного
    `owner_uuid` и режима доступа к публичным книгам правил.

    Ошибка намеренно не разделяет случаи "не найдено" и "нет доступа",
    чтобы внешний API мог вернуть единый ответ и не раскрывать существование
    приватных сущностей.
    """


class RaceValidationError(ValueError):
    """Ошибка доменной валидации расы.

    Используется, когда операция нарушает правила структуры данных:
    например, родительская раса находится в другой книге правил, родителем
    выбрана сама обновляемая раса, родителем выбрана одна из дочерних рас
    или в запросе обновления не передано ни одного изменяемого поля.
    """


class RaceConflictError(ValueError):
    """Ошибка конфликта уникальности расы.

    Используется, когда имя расы уже занято внутри той же книги правил.
    Обычно соответствует нарушению ограничения уникальности по паре
    `ruleset_uuid` и `name`.
    """


class RaceController(Database):
    """Контроллер для работы с таблицей `races`.

    Инкапсулирует SQL-запросы, связанные с расами персонажей:
    создание, получение, постраничное получение, частичное обновление
    и удаление записей.

    Все операции изменения выполняются через проверку владельца связанной
    книги правил. Это не позволяет пользователю создать, изменить или удалить
    расу в чужой приватной книге правил.

    Операции чтения могут работать в двух режимах:
    только для книг правил владельца или для книг правил владельца вместе
    с публичными книгами правил.
    """

    @staticmethod
    def as_model(row: RowMapping) -> Race:
        """Convert the ORM entity into the corresponding Pydantic model."""
        return Race(
            uuid=row["uuid"],
            ruleset_uuid=row["ruleset_uuid"],
            parent_uuid=row["parent_uuid"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def insert(
        self,
        data: RaceCreated,
        owner_uuid: UUID,
        _session: AsyncSession | None = None,
    ) -> UUID:
        """Создать новую расу в книге правил текущего пользователя.

        Создаёт новую запись в таблице `races`, предварительно проверяя,
        что указанная книга правил существует и принадлежит пользователю
        с UUID `owner_uuid`.

        Если для создаваемой расы передан `parent_uuid`, контроллер проверяет,
        что родительская раса принадлежит той же книге правил. Это защищает
        иерархию рас от связей между разными книгами правил.

        Вставка выполняется через CTE:
        сначала определяется доступная книга правил и валидность родителя,
        затем выполняется `INSERT`. При конфликте имени внутри книги правил
        вставка пропускается через `ON CONFLICT DO NOTHING`, после чего метод
        преобразует результат в доменную ошибку `RaceConflictError`.

        Args:
            data (RaceCreated): Данные создаваемой расы. Содержит UUID книги
                правил, опциональный UUID родительской расы, название и описание.
            owner_uuid (UUID): UUID пользователя, который должен быть владельцем
                книги правил.
            _session (AsyncSession | None): Внешняя асинхронная SQLAlchemy-сессия.
                Если передана, используется она. Если не передана, контроллер
                создаёт сессию самостоятельно.

        Returns:
            UUID: UUID созданной расы.

        Raises:
            RaceNotFoundError: Если книга правил не найдена или не принадлежит
                текущему пользователю.
            RaceValidationError: Если родительская раса передана, но не относится
                к той же книге правил.
            RaceConflictError: Если имя расы уже используется в указанной книге
                правил.
        """
        race_uuid = uuid.uuid4()
        now = datetime.datetime.now(tz=datetime.UTC)
        sql = text(
            """
            WITH context AS (
                SELECT
                    rulesets.uuid AS ruleset_uuid,
                    (
                        :parent_uuid IS NULL
                        OR EXISTS (
                            SELECT 1
                            FROM races AS parent
                            WHERE parent.uuid = :parent_uuid
                              AND parent.ruleset_uuid = rulesets.uuid
                        )
                    ) AS parent_valid
                FROM rulesets
                WHERE rulesets.uuid = :ruleset_uuid
                  AND rulesets.owner_uuid = :owner_uuid
            ),
            inserted AS (
                INSERT INTO races (
                    uuid,
                    ruleset_uuid,
                    parent_uuid,
                    name,
                    description,
                    created_at,
                    updated_at
                )
                SELECT
                    :uuid,
                    context.ruleset_uuid,
                    :parent_uuid,
                    :name,
                    :description,
                    :created_at,
                    :updated_at
                FROM context
                WHERE context.parent_valid
                ON CONFLICT (ruleset_uuid, name) DO NOTHING
                RETURNING uuid
            )
            SELECT
                EXISTS (SELECT 1 FROM context) AS ruleset_found,
                COALESCE((SELECT parent_valid FROM context), FALSE) AS parent_valid,
                (SELECT uuid FROM inserted) AS inserted_uuid
            """
        ).bindparams(bindparam("parent_uuid", type_=SqlUUID))
        params = {
            "uuid": race_uuid,
            "ruleset_uuid": data.ruleset_uuid,
            "owner_uuid": owner_uuid,
            "parent_uuid": data.parent_uuid,
            "name": data.name,
            "description": data.description,
            "created_at": now,
            "updated_at": now,
        }

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            row = result.mappings().one()

        if not row["ruleset_found"]:
            raise RaceNotFoundError("Книга правил не найдена")
        if not row["parent_valid"]:
            raise RaceValidationError("Родительская раса должна принадлежать той же книге правил")
        if row["inserted_uuid"] is None:
            raise RaceConflictError("Название расы уже используется в этой книге правил")

        return row["inserted_uuid"]

    async def get(
        self,
        race_uuid: UUID,
        owner_uuid: UUID | None = None,
        include_public: bool = False,
        _session: AsyncSession | None = None,
    ) -> Race | None:
        """Получить расу по UUID с учётом прав доступа.

        Ищет расу по UUID и возвращает её только в том случае, если она доступна
        текущему контексту доступа.

        Если `owner_uuid` не передан, метод выполняет поиск без ограничения
        по владельцу книги правил. Если `owner_uuid` передан, доступ ограничивается
        книгами правил этого пользователя. При `include_public=True` дополнительно
        разрешается чтение рас из публичных книг правил.

        Args:
            race_uuid (UUID): UUID расы, которую необходимо получить.
            owner_uuid (UUID | None): UUID пользователя, относительно которого
                проверяется доступ к связанной книге правил. Если не передан,
                проверка владельца не применяется.
            include_public (bool): Разрешить ли чтение рас из публичных книг
                правил, если они не принадлежат пользователю.
            _session (AsyncSession | None): Внешняя асинхронная SQLAlchemy-сессия.
                Если передана, используется она. Если не передана, контроллер
                создаёт сессию самостоятельно.

        Returns:
            Race | None: Модель расы, если запись найдена и доступна.
            Если запись отсутствует или недоступна, возвращается None.
        """
        access_filter = ""
        params: dict[str, Any] = {"uuid": race_uuid}

        if owner_uuid is not None:
            params["owner_uuid"] = owner_uuid
            if include_public:
                access_filter = " AND (rulesets.owner_uuid = :owner_uuid OR rulesets.is_public IS TRUE)"
            else:
                access_filter = " AND rulesets.owner_uuid = :owner_uuid"

        sql = text(
            """
            SELECT
                races.uuid,
                races.ruleset_uuid,
                races.parent_uuid,
                races.name,
                races.description,
                races.created_at,
                races.updated_at
            FROM races
            JOIN rulesets ON rulesets.uuid = races.ruleset_uuid
            WHERE races.uuid = :uuid
            """
            + access_filter
        )

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            row = result.mappings().one_or_none()

        return None if row is None else self.as_model(row)

    async def list_by_ruleset(
        self,
        ruleset_uuid: UUID,
        owner_uuid: UUID | None = None,
        include_public: bool = False,
        cursor: UUID | None = None,
        limit: int = 50,
        _session: AsyncSession | None = None,
    ) -> list[Race]:
        """Получить страницу рас из указанной книги правил.

        Возвращает список рас, относящихся к книге правил `ruleset_uuid`,
        с учётом прав доступа текущего пользователя.

        Если `owner_uuid` передан, контроллер проверяет, что книга правил
        принадлежит этому пользователю. При `include_public=True` также разрешается
        чтение рас из публичных книг правил. Если книга правил не найдена или
        недоступна, выбрасывается `RaceNotFoundError`.

        Для постраничной выдачи используется устойчивый порядок по паре
        `(created_at, uuid)`. Внешним курсором остаётся UUID последней записи
        предыдущей страницы: контроллер находит её позицию по времени создания
        и возвращает следующие записи. Размер страницы ограничивается `limit`.

        Args:
            ruleset_uuid (UUID): UUID книги правил, для которой нужно получить
                список рас.
            owner_uuid (UUID | None): UUID пользователя, относительно которого
                проверяется доступ к книге правил. Если не передан, проверка
                владельца не применяется.
            include_public (bool): Разрешить ли чтение рас из публичной книги
                правил, если она не принадлежит пользователю.
            cursor (UUID | None): UUID последней записи предыдущей страницы.
                Позиция курсора определяется по её `created_at` и UUID.
            limit (int): Максимальное количество записей на странице. Допустимый
                диапазон: от 1 до 100 включительно.
            _session (AsyncSession | None): Внешняя асинхронная SQLAlchemy-сессия.
                Если передана, используется она. Если не передана, контроллер
                создаёт сессию самостоятельно.

        Returns:
            list[Race]: Список рас, доступных пользователю в рамках указанной
            книги правил.

        Raises:
            ValueError: Если `limit` находится вне диапазона от 1 до 100.
            RaceNotFoundError: Если книга правил не найдена или недоступна
                текущему пользователю.
        """
        if not 1 <= limit <= 100:
            raise ValueError("Параметр limit должен быть от 1 до 100")

        params: dict[str, Any] = {
            "ruleset_uuid": ruleset_uuid,
            "limit": limit,
        }
        access_filter = ""
        cursor_filter = ""

        if owner_uuid is not None:
            params["owner_uuid"] = owner_uuid
            if include_public:
                access_filter = " AND (rulesets.owner_uuid = :owner_uuid OR rulesets.is_public IS TRUE)"
            else:
                access_filter = " AND rulesets.owner_uuid = :owner_uuid"

        if cursor is not None:
            params["cursor"] = cursor
            cursor_filter = """
                AND EXISTS (
                    SELECT 1
                    FROM races AS cursor_race
                    WHERE cursor_race.uuid = :cursor
                      AND cursor_race.ruleset_uuid = :ruleset_uuid
                      AND (races.created_at, races.uuid)
                          > (cursor_race.created_at, cursor_race.uuid)
                )
            """

        sql = text(
            """
            WITH accessible_ruleset AS (
                SELECT rulesets.uuid
                FROM rulesets
                WHERE rulesets.uuid = :ruleset_uuid
            """
            + access_filter
            + """
            ),
            page AS (
                SELECT
                    races.uuid,
                    races.ruleset_uuid,
                    races.parent_uuid,
                    races.name,
                    races.description,
                    races.created_at,
                    races.updated_at
                FROM races
                JOIN accessible_ruleset
                  ON accessible_ruleset.uuid = races.ruleset_uuid
                WHERE TRUE
            """
            + cursor_filter
            + """
                ORDER BY races.created_at, races.uuid
                LIMIT :limit
            )
            SELECT
                EXISTS (SELECT 1 FROM accessible_ruleset) AS ruleset_found,
                page.uuid,
                page.ruleset_uuid,
                page.parent_uuid,
                page.name,
                page.description,
                page.created_at,
                page.updated_at
            FROM (SELECT 1) AS singleton
            LEFT JOIN page ON TRUE
            ORDER BY page.created_at, page.uuid
            """
        )

        async with self.session(_session) as session:
            result = await session.execute(sql, params)
            rows = result.mappings().all()

        if not rows[0]["ruleset_found"]:
            raise RaceNotFoundError("Книга правил не найдена")

        return [self.as_model(row) for row in rows if row["uuid"] is not None]

    async def update(
        self,
        data: RaceUpdated,
        owner_uuid: UUID,
        _session: AsyncSession | None = None,
    ) -> UUID:
        """Частично обновить расу в книге правил текущего пользователя.

        Обновляет только поля, явно переданные в модели `RaceUpdated`.
        UUID расы используется для поиска записи и не считается обновляемым полем.

        Перед обновлением контроллер проверяет, что раса существует и относится
        к книге правил, принадлежащей пользователю `owner_uuid`.

        При изменении `parent_uuid` выполняется дополнительная проверка иерархии:
        новая родительская раса должна принадлежать той же книге правил, не должна
        совпадать с обновляемой расой и не должна находиться внутри её дочернего
        поддерева. Это предотвращает появление циклов в дереве наследования рас.

        Обновление выполняется через CTE и рекурсивный запрос `descendants`,
        который находит всех потомков обновляемой расы перед проверкой нового
        родителя.

        Args:
            data (RaceUpdated): Данные для частичного обновления расы.
                Обязательно содержит UUID расы. Остальные поля обновляются только
                при явной передаче.
            owner_uuid (UUID): UUID пользователя, который должен быть владельцем
                книги правил, содержащей обновляемую расу.
            _session (AsyncSession | None): Внешняя асинхронная SQLAlchemy-сессия.
                Если передана, используется она. Если не передана, контроллер
                создаёт сессию самостоятельно.

        Returns:
            UUID: UUID обновлённой расы.

        Raises:
            RaceValidationError: Если не передано ни одного поля для обновления,
                если передано запрещённое поле, если обязательное поле передано
                как None, или если новый родитель нарушает правила иерархии.
            RaceNotFoundError: Если раса не найдена или не принадлежит книге правил
                текущего пользователя.
            RaceConflictError: Если новое имя расы уже используется в той же книге
                правил.
            IntegrityError: Если БД вернула ошибку целостности, не обработанную
                как доменный конфликт имени.
        """
        fields_to_update = data.model_fields_set - {"uuid"}
        if not fields_to_update:
            raise RaceValidationError("Не переданы поля для обновления расы")

        allowed_fields = {"parent_uuid", "name", "description"}
        nullable_fields = {"parent_uuid"}
        details: list[str] = []
        params: dict[str, Any] = {
            "uuid": data.uuid,
            "owner_uuid": owner_uuid,
            "updated_at": datetime.datetime.now(tz=datetime.UTC),
            "validate_parent": "parent_uuid" in fields_to_update,
            "parent_uuid": data.parent_uuid,
        }

        for field_name in sorted(fields_to_update):
            if field_name not in allowed_fields:
                raise RaceValidationError(f"Поле {field_name!r} нельзя обновлять")

            value = getattr(data, field_name)
            if value is None and field_name not in nullable_fields:
                raise RaceValidationError(f"Поле {field_name!r} не может быть null")

            details.append(f"{field_name} = :{field_name}")
            params[field_name] = value

        details.append("updated_at = :updated_at")
        sql = text(
            f"""
            WITH RECURSIVE descendants(uuid) AS (
                SELECT child.uuid
                FROM races AS child
                WHERE child.parent_uuid = :uuid
                UNION
                SELECT child.uuid
                FROM races AS child
                JOIN descendants ON child.parent_uuid = descendants.uuid
            ),
            candidate AS (
                SELECT
                    races.uuid,
                    races.ruleset_uuid,
                    CASE
                        WHEN NOT :validate_parent THEN TRUE
                        WHEN :parent_uuid IS NULL THEN TRUE
                        ELSE (
                            :parent_uuid <> races.uuid
                            AND NOT EXISTS (
                                SELECT 1 FROM descendants WHERE uuid = :parent_uuid
                            )
                            AND EXISTS (
                                SELECT 1
                                FROM races AS parent
                                WHERE parent.uuid = :parent_uuid
                                  AND parent.ruleset_uuid = races.ruleset_uuid
                            )
                        )
                    END AS parent_valid
                FROM races
                JOIN rulesets ON rulesets.uuid = races.ruleset_uuid
                WHERE races.uuid = :uuid
                  AND rulesets.owner_uuid = :owner_uuid
            ),
            updated AS (
                UPDATE races
                SET {", ".join(details)}
                FROM candidate
                WHERE races.uuid = candidate.uuid
                  AND candidate.parent_valid
                RETURNING races.uuid
            )
            SELECT
                EXISTS (SELECT 1 FROM candidate) AS race_found,
                COALESCE((SELECT parent_valid FROM candidate), FALSE) AS parent_valid,
                (SELECT uuid FROM updated) AS updated_uuid
            """
        ).bindparams(bindparam("parent_uuid", type_=SqlUUID))

        try:
            async with self.session(_session) as session:
                result = await session.execute(sql, params)
                row = result.mappings().one()
        except IntegrityError as error:
            constraint_name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            if constraint_name == "uq_races_ruleset_uuid_name":
                raise RaceConflictError("Название расы уже используется в этой книге правил") from error
            raise

        if not row["race_found"]:
            raise RaceNotFoundError("Раса не найдена")
        if not row["parent_valid"]:
            raise RaceValidationError(
                "Родительская раса должна принадлежать той же книге правил "
                "и не может находиться в поддереве обновляемой расы"
            )

        return row["updated_uuid"]

    async def delete(
        self,
        race_uuid: UUID,
        owner_uuid: UUID,
        _session: AsyncSession | None = None,
    ) -> None:
        """Удалить расу из книги правил текущего пользователя.

        Выполняет физическое удаление записи из таблицы `races`.
        Удаление разрешено только в том случае, если раса относится к книге правил,
        принадлежащей пользователю `owner_uuid`.

        Проверка доступа выполняется через `DELETE ... USING rulesets`, чтобы
        операция удаления и проверка владельца связанной книги правил происходили
        одним SQL-запросом.

        Args:
            race_uuid (UUID): UUID расы, которую необходимо удалить.
            owner_uuid (UUID): UUID пользователя, который должен быть владельцем
                книги правил, содержащей удаляемую расу.
            _session (AsyncSession | None): Внешняя асинхронная SQLAlchemy-сессия.
                Если передана, используется она. Если не передана, контроллер
                создаёт сессию самостоятельно.

        Returns:
            None: Метод ничего не возвращает при успешном удалении.

        Raises:
            RaceNotFoundError: Если раса не найдена или не принадлежит книге правил
                текущего пользователя.
        """
        sql = text(
            """
            DELETE FROM races
            USING rulesets
            WHERE races.uuid = :uuid
              AND rulesets.uuid = races.ruleset_uuid
              AND rulesets.owner_uuid = :owner_uuid
            RETURNING races.uuid
            """
        )

        async with self.session(_session) as session:
            result = await session.execute(sql, {"uuid": race_uuid, "owner_uuid": owner_uuid})
            deleted_uuid = result.scalar_one_or_none()

        if deleted_uuid is None:
            raise RaceNotFoundError("Раса не найдена")
