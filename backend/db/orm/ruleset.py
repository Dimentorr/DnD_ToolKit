"""Название: ruleset.py

Путь: backend/db/orm/ruleset.py
Автор: stepapetruk@ya.ru
Дата: [31.05.2026]::2026-May-Sunday
Описание:

Описание файла.
"""

import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Boolean, CheckConstraint, ForeignKey, String, Text, func
from sqlalchemy import UUID as SqlUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.model.ruleset import Ruleset as RulesetModel
from backend.db.orm.base import Base
from backend.models.ruleset import Status

if TYPE_CHECKING:
    from backend.db.orm.datasheets import Datasheet
    from backend.db.orm.race import Race
    from backend.db.orm.user import User


class Ruleset(Base):
    """ORM-модель таблицы rulesets"""

    __tablename__ = "rulesets"

    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 255", name="ck_rulesets_name_length"),
        CheckConstraint("status IN ('inwork', 'active', 'archive')", name="ck_rulesets_status"),
        CheckConstraint("parent_uuid IS NULL OR parent_uuid <> uuid", name="ck_rulesets_parent_not_self"),
    )
    uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    owner_uuid: Mapped[UUID | None] = mapped_column(
        SqlUUID,
        ForeignKey(
            "users.uuid",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    parent_uuid: Mapped[UUID | None] = mapped_column(
        SqlUUID,
        ForeignKey(
            "rulesets.uuid",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Описание книги правил",
    )

    version: Mapped[str] = mapped_column(
        String(24),
        default="0.0.1",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(24),
        default=Status.InWork.value,
        nullable=False,
    )

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        comment="общедоступная книга правил",
        default=False,
        nullable=False,
    )

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

    owner: Mapped["User | None"] = relationship(back_populates="rulesets")
    parent: Mapped["Ruleset | None"] = relationship(
        remote_side="Ruleset.uuid",
        back_populates="children",
    )
    children: Mapped[list["Ruleset"]] = relationship(
        back_populates="parent",
        passive_deletes=True,
    )
    races: Mapped[list["Race"]] = relationship(
        back_populates="ruleset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    datasheets: Mapped[list["Datasheet"]] = relationship(back_populates="ruleset", passive_deletes=True)

    def as_model(self) -> RulesetModel:
        """Convert the ORM entity into the corresponding Pydantic model."""
        return RulesetModel(
            uuid=self.uuid,
            owner_uuid=self.owner_uuid,
            parent_uuid=self.parent_uuid,
            name=self.name,
            description=self.description,
            version=self.version,
            status=Status(self.status),
            is_public=self.is_public,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
