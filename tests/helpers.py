"""Название: helpers.py

Путь: tests/helpers.py
Автор: stepapetruk@ya.ru
Дата: [19.07.2026]::2026-July-Sunday
Описание:

Вспомогательные типы и фабрики тестовых данных.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from backend.db.orm.race import Race
from backend.db.orm.ruleset import Ruleset
from backend.db.orm.user import User
from backend.models.ruleset import Status


@dataclass(frozen=True, slots=True)
class PostgresHarness:
    """Подключение к изолированной тестовой схеме PostgreSQL."""

    url: str = field(repr=False)
    engine: AsyncEngine


async def create_user(
    session: AsyncSession,
    *,
    name_prefix: str = "user",
) -> UUID:
    """Создать пользователя и вернуть его UUID."""
    identifier = uuid4().hex
    user_uuid = uuid4()
    session.add(
        User(
            uuid=user_uuid,
            name=f"{name_prefix}_{identifier[:10]}",
            email=f"{identifier}@example.test",
            password="test-password-hash",
        )
    )
    await session.flush()
    return user_uuid


async def create_ruleset(
    session: AsyncSession,
    *,
    owner_uuid: UUID,
    is_public: bool = False,
    name: str | None = None,
) -> UUID:
    """Создать книгу правил и вернуть её UUID."""
    ruleset_uuid = uuid4()
    session.add(
        Ruleset(
            uuid=ruleset_uuid,
            owner_uuid=owner_uuid,
            name=name or f"Книга {uuid4().hex[:10]}",
            description="Тестовая книга правил",
            version="1.0.0",
            status=Status.InWork.value,
            is_public=is_public,
        )
    )
    await session.flush()
    return ruleset_uuid


async def create_race(
    session: AsyncSession,
    *,
    ruleset_uuid: UUID,
    name: str | None = None,
    parent_uuid: UUID | None = None,
    race_uuid: UUID | None = None,
    created_at: datetime.datetime | None = None,
) -> UUID:
    """Создать расу напрямую через ORM и вернуть её UUID."""
    result_uuid = race_uuid or uuid4()
    race = Race(
        uuid=result_uuid,
        ruleset_uuid=ruleset_uuid,
        parent_uuid=parent_uuid,
        name=name or f"Раса {uuid4().hex[:10]}",
        description="Тестовое описание расы",
    )
    if created_at is not None:
        race.created_at = created_at
        race.updated_at = created_at
    session.add(race)
    await session.flush()
    return result_uuid
