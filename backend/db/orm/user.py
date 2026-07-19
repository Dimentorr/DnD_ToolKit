"""Название: user.py

Путь: backend/db/orm/user.py
Автор: stepapetruk@ya.ru
Дата: [03.05.2026]::2026-May-Sunday
Описание:

Описание файла.
"""

import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, CheckConstraint, ForeignKey, String, func
from sqlalchemy import UUID as SqlUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.model.token import TokenData
from backend.db.model.user import User as UserModel
from backend.db.orm.base import Base

if TYPE_CHECKING:
    from backend.db.orm.datasheets import Datasheet
    from backend.db.orm.ruleset import Ruleset


class User(Base):
    """ORM-модель таблицы users"""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("char_length(name) BETWEEN 3 AND 64", name="ck_users_name_length"),)

    uuid: Mapped[UUID] = mapped_column(
        SqlUUID,
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        unique=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
        index=True,
        unique=True,
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="hashed password",
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    tokens: Mapped[list["Token"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    datasheets: Mapped[list["Datasheet"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    rulesets: Mapped[list["Ruleset"]] = relationship(back_populates="owner")

    def as_model(self) -> UserModel:
        """Convert the ORM entity into a public user model."""
        return UserModel(
            uuid=self.uuid,
            name=self.name,
            email=self.email,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class Token(Base):
    """ORM-модель таблицы tokens"""

    __tablename__ = "tokens"
    __table_args__ = (CheckConstraint("char_length(token) = 64", name="ck_tokens_hash_length"),)

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
    token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="hashed token",
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime.datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
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

    user: Mapped["User"] = relationship(back_populates="tokens")

    def as_model(self) -> TokenData:
        """Convert the ORM entity into a token data model."""
        return TokenData(
            uuid=self.uuid,
            user_uuid=self.user_uuid,
            token=self.token,
            expires_at=self.expires_at,
            revoked_at=self.revoked_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def __repr__(self) -> str:
        """Return a representation that does not expose the token hash."""
        return (
            f"Token(uuid={self.uuid!r}, user_uuid={self.user_uuid!r}, "
            f"expires_at={self.expires_at!r}, revoked_at={self.revoked_at!r})"
        )
