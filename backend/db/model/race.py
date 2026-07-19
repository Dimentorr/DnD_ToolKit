"""Название: race.py

Путь: backend/db/model/race.py
Автор: stepapetruk@ya.ru
Дата: [19.07.2026]::2026-July-Sunday
Описание:

Pydantic-модели рас персонажей.

Содержит модели для создания, частичного обновления и чтения рас персонажей
на уровне слоя работы с БД.

Раса относится к конкретной книге правил через `ruleset_uuid` и может иметь
родительскую расу через `parent_uuid`. Родительская связь используется для
построения иерархии или производных вариантов рас внутри одной книги правил.
"""

import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from backend.models.base import BasePydanticModel


class RaceCreated(BasePydanticModel):
    """Pydantic-модель данных для создания расы персонажа.

    Используется при передаче данных из API-слоя в контроллер БД.
    Содержит UUID книги правил, опциональный UUID родительской расы,
    название и описание создаваемой расы.

    Поле `ruleset_uuid` определяет книгу правил, внутри которой будет создана
    раса. Поле `parent_uuid` может использоваться для создания производной расы,
    но корректность родительской связи проверяется на уровне контроллера БД.

    Attributes:
        ruleset_uuid (UUID): UUID книги правил, к которой относится раса.
        parent_uuid (UUID | None): UUID родительской расы. Если не передан,
            раса считается корневой в своей иерархии.
        name (str): Название расы. Должно содержать от 1 до 255 символов.
        description (str): Описание расы.
    """

    ruleset_uuid: UUID
    parent_uuid: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)

    def as_dict(self) -> dict[str, Any]:
        """Convert the model to a JSON-compatible dictionary."""
        return self.model_dump(mode="json")


class RaceUpdated(BasePydanticModel):
    """Pydantic-модель данных для частичного обновления расы персонажа.

    Используется при PATCH-обновлении существующей расы. Поле `uuid`
    обязательно и определяет обновляемую запись. Остальные поля являются
    опциональными и обновляются только при явной передаче в запросе.

    Модель допускает явную передачу `parent_uuid=None`, чтобы отвязать расу
    от родительской записи. Поэтому при преобразовании модели в словарь важно
    использовать `exclude_unset=True`, а не `exclude_none=True`.

    Attributes:
        uuid (UUID): UUID обновляемой расы.
        parent_uuid (UUID | None): Новый UUID родительской расы или None,
            если связь с родителем нужно удалить.
        name (str | None): Новое название расы. Если передано, должно содержать
            от 1 до 255 символов.
        description (str | None): Новое описание расы.
    """

    uuid: UUID
    parent_uuid: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)

    def as_dict(self) -> dict[str, Any]:
        """Convert only explicitly supplied fields to a dictionary."""
        return self.model_dump(mode="json", exclude_unset=True)


class Race(RaceCreated):
    """Полная Pydantic-модель расы персонажа.

    Используется для возврата данных из слоя БД и API-ответов.
    Расширяет модель `RaceCreated` техническими полями записи:
    UUID самой расы и временными метками создания и обновления.

    Attributes:
        uuid (UUID): UUID расы.
        created_at (datetime.datetime): Дата и время создания записи.
        updated_at (datetime.datetime): Дата и время последнего обновления записи.
    """

    uuid: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
