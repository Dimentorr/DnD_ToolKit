"""Интеграционные тесты чтения и пагинации рас."""

import datetime
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.race import RaceController, RaceNotFoundError
from tests.helpers import (
    PostgresHarness,
    create_race,
    create_ruleset,
    create_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_public_race_is_visible_to_another_user(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Разрешить чтение расы из публичной книги правил."""
    owner_uuid = await create_user(db_session, name_prefix="owner")
    reader_uuid = await create_user(db_session, name_prefix="reader")
    ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        is_public=True,
    )
    race_uuid = await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        name="Тифлинг",
    )
    controller = RaceController(postgres.url)

    race = await controller.get(
        race_uuid,
        owner_uuid=reader_uuid,
        include_public=True,
        _session=db_session,
    )

    assert race is not None
    assert race.uuid == race_uuid


async def test_private_race_is_hidden_from_another_user(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Скрыть расу из чужой приватной книги правил."""
    owner_uuid = await create_user(db_session, name_prefix="owner")
    reader_uuid = await create_user(db_session, name_prefix="reader")
    ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        is_public=False,
    )
    race_uuid = await create_race(db_session, ruleset_uuid=ruleset_uuid)
    controller = RaceController(postgres.url)

    race = await controller.get(
        race_uuid,
        owner_uuid=reader_uuid,
        include_public=True,
        _session=db_session,
    )

    assert race is None


async def test_empty_accessible_ruleset_returns_empty_list(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Отличить пустую доступную книгу правил от недоступной."""
    owner_uuid = await create_user(db_session, name_prefix="owner")
    reader_uuid = await create_user(db_session, name_prefix="reader")
    public_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        is_public=True,
    )
    private_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        is_public=False,
    )
    controller = RaceController(postgres.url)

    races = await controller.list_by_ruleset(
        public_ruleset_uuid,
        owner_uuid=reader_uuid,
        include_public=True,
        _session=db_session,
    )

    assert races == []
    with pytest.raises(RaceNotFoundError):
        await controller.list_by_ruleset(
            private_ruleset_uuid,
            owner_uuid=reader_uuid,
            include_public=True,
            _session=db_session,
        )


async def test_pagination_uses_creation_time_then_uuid(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Сортировать страницы по времени создания, а не случайному UUID."""
    owner_uuid = await create_user(db_session)
    ruleset_uuid = await create_ruleset(db_session, owner_uuid=owner_uuid)
    earlier_uuid = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
    later_uuid = UUID("00000000-0000-4000-8000-000000000001")
    earlier_at = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    later_at = earlier_at + datetime.timedelta(seconds=1)
    await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        name="Ранняя",
        race_uuid=earlier_uuid,
        created_at=earlier_at,
    )
    await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        name="Поздняя",
        race_uuid=later_uuid,
        created_at=later_at,
    )
    controller = RaceController(postgres.url)

    first_page = await controller.list_by_ruleset(
        ruleset_uuid,
        owner_uuid=owner_uuid,
        cursor=None,
        limit=1,
        _session=db_session,
    )
    second_page = await controller.list_by_ruleset(
        ruleset_uuid,
        owner_uuid=owner_uuid,
        cursor=first_page[-1].uuid,
        limit=1,
        _session=db_session,
    )

    assert [race.uuid for race in first_page] == [earlier_uuid]
    assert [race.uuid for race in second_page] == [later_uuid]
