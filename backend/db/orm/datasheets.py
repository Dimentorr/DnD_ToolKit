"""Название: datasheets.py

Путь: backend/db/orm/datasheets.py
Автор: stepapetruk@ya.ru
Дата: [31.05.2026]::2026-May-Sunday
Описание:

Описание файла.
"""

import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, String, func
from sqlalchemy import UUID as SqlUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.model.datasheet import Datasheet as DatasheetModel
from backend.db.orm.base import Base
from backend.models.datasheet import Features, Inventory, Stats, Wallet

if TYPE_CHECKING:
    from backend.db.orm.race import Race
    from backend.db.orm.ruleset import Ruleset
    from backend.db.orm.user import User


class Datasheet(Base):
    """ORM-модель таблицы datasheets"""

    __tablename__ = "datasheets"
    __table_args__ = (CheckConstraint("char_length(name) BETWEEN 1 AND 255", name="ck_datasheets_name_length"),)

    uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    user_uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        ForeignKey("users.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ruleset_uuid: Mapped[UUID | None] = mapped_column(
        SqlUUID,
        ForeignKey("rulesets.uuid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    race_uuid: Mapped[UUID | None] = mapped_column(
        SqlUUID,
        ForeignKey("races.uuid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    stats: Mapped[dict[str, int]] = mapped_column(
        MutableDict.as_mutable(JSONB),
        default=lambda: Stats().as_dict(),
        nullable=False,
    )

    wallet: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB),
        default=lambda: Wallet().as_dict(),
        comment="кошель персонажа",
        nullable=False,
    )
    features: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB),
        default=lambda: Features().as_dict(),
        comment="черты персонажа",
        nullable=False,
    )

    inventory: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB),
        default=lambda: Inventory().as_dict(),
        comment="инвентарь персонажа",
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

    user: Mapped["User"] = relationship(back_populates="datasheets")
    ruleset: Mapped["Ruleset | None"] = relationship(back_populates="datasheets")
    race: Mapped["Race | None"] = relationship(back_populates="datasheets")

    def as_model(self) -> DatasheetModel:
        """Convert the ORM entity into the corresponding Pydantic model."""
        return DatasheetModel(
            uuid=self.uuid,
            user_uuid=self.user_uuid,
            ruleset_uuid=self.ruleset_uuid,
            name=self.name,
            race=self.race_uuid,
            stats=Stats.model_validate(self.stats),
            wallet=Wallet.model_validate(self.wallet),
            features=Features.model_validate(self.features),
            inventory=Inventory.model_validate(self.inventory),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
