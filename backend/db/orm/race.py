"""Название: race.py

Путь: backend/db/orm/race.py
Автор: stepapetruk@ya.ru
Дата: [19.07.2026]::2026-July-Sunday
Описание:

SQLAlchemy ORM-модель рас персонажей.

Описывает таблицу `races`, в которой хранятся расы, относящиеся к книгам
правил. Каждая раса принадлежит конкретному ruleset через `ruleset_uuid`
и может ссылаться на родительскую расу через `parent_uuid`.

Модель поддерживает древовидную иерархию рас внутри одной книги правил:
например, базовая раса может иметь производные варианты или подрасы.
Ограничения таблицы запрещают пустые названия, прямую ссылку расы на саму себя
и дублирование названия расы внутри одного ruleset.

Для преобразования ORM-сущности в Pydantic-модель слоя БД используется метод
`as_model`.
"""

import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy import UUID as SqlUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.model.race import Race as RaceModel
from backend.db.orm.base import Base

if TYPE_CHECKING:
    from backend.db.orm.datasheets import Datasheet
    from backend.db.orm.ruleset import Ruleset


class Race(Base):
    """ORM-модель таблицы `races`.

    Представляет расу персонажа внутри конкретной книги правил.

    Связи модели:
        - `ruleset` — книга правил, к которой относится раса.
        - `parent` — родительская раса, если текущая раса является производной.
        - `children` — дочерние расы, ссылающиеся на текущую расу.
        - `datasheets` — листы персонажей, использующие эту расу.

    Ограничения таблицы:
        - `ck_races_name_length` проверяет, что длина названия находится
        в диапазоне от 1 до 255 символов.
        - `ck_races_parent_not_self` запрещает прямую ссылку расы на саму себя.
        - `uq_races_ruleset_uuid_name` запрещает две расы с одинаковым названием
        внутри одной книги правил.

    Важно:
        Ограничение `ck_races_parent_not_self` защищает только от прямой ссылки
        `parent_uuid = uuid`. Более сложные циклы, например A -> B -> C -> A,
        должны проверяться на уровне контроллера или отдельной доменной логики.
    """

    __tablename__ = "races"
    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 255", name="ck_races_name_length"),
        CheckConstraint("parent_uuid IS NULL OR parent_uuid <> uuid", name="ck_races_parent_not_self"),
        UniqueConstraint("ruleset_uuid", "name", name="uq_races_ruleset_uuid_name"),
    )

    uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    ruleset_uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        ForeignKey("rulesets.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_uuid: Mapped[UUID | None] = mapped_column(
        SqlUUID,
        ForeignKey("races.uuid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    ruleset: Mapped["Ruleset"] = relationship(back_populates="races")
    parent: Mapped["Race | None"] = relationship(
        remote_side="Race.uuid",
        back_populates="children",
    )
    children: Mapped[list["Race"]] = relationship(
        back_populates="parent",
        passive_deletes=True,
    )
    datasheets: Mapped[list["Datasheet"]] = relationship(
        back_populates="race",
        passive_deletes=True,
    )

    def as_model(self) -> RaceModel:
        """Convert the ORM entity into the corresponding Pydantic model."""
        return RaceModel(
            uuid=self.uuid,
            ruleset_uuid=self.ruleset_uuid,
            parent_uuid=self.parent_uuid,
            name=self.name,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
