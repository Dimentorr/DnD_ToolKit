"""Интеграционные тесты создания рас."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.race import (
    RaceConflictError,
    RaceController,
    RaceNotFoundError,
    RaceValidationError,
)
from backend.db.model.race import RaceCreated
from tests.helpers import (
    PostgresHarness,
    create_race,
    create_ruleset,
    create_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_cannot_create_race_in_foreign_private_ruleset(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Запретить создание расы в чужой приватной книге правил."""
    owner_uuid = await create_user(db_session, name_prefix="owner")
    intruder_uuid = await create_user(db_session, name_prefix="intruder")
    ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        is_public=False,
    )
    controller = RaceController(postgres.url)

    with pytest.raises(RaceNotFoundError):
        await controller.insert(
            RaceCreated(
                ruleset_uuid=ruleset_uuid,
                name="Эльф",
                description="Описание",
            ),
            owner_uuid=intruder_uuid,
            _session=db_session,
        )


async def test_parent_must_belong_to_same_ruleset(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Запретить родителя из другой книги правил."""
    owner_uuid = await create_user(db_session)
    first_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
    )
    second_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
    )
    parent_uuid = await create_race(
        db_session,
        ruleset_uuid=first_ruleset_uuid,
        name="Родитель",
    )
    controller = RaceController(postgres.url)

    with pytest.raises(RaceValidationError):
        await controller.insert(
            RaceCreated(
                ruleset_uuid=second_ruleset_uuid,
                parent_uuid=parent_uuid,
                name="Неверный потомок",
                description="Описание",
            ),
            owner_uuid=owner_uuid,
            _session=db_session,
        )


async def test_name_is_unique_inside_ruleset(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Запретить одинаковые названия внутри одной книги правил."""
    owner_uuid = await create_user(db_session)
    ruleset_uuid = await create_ruleset(db_session, owner_uuid=owner_uuid)
    controller = RaceController(postgres.url)
    data = RaceCreated(
        ruleset_uuid=ruleset_uuid,
        name="Дварф",
        description="Описание",
    )

    await controller.insert(
        data,
        owner_uuid=owner_uuid,
        _session=db_session,
    )

    with pytest.raises(RaceConflictError):
        await controller.insert(
            data,
            owner_uuid=owner_uuid,
            _session=db_session,
        )


async def test_same_name_is_allowed_in_different_rulesets(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Разрешить одинаковое название в разных книгах правил."""
    owner_uuid = await create_user(db_session)
    first_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
    )
    second_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
    )
    controller = RaceController(postgres.url)

    first_uuid = await controller.insert(
        RaceCreated(
            ruleset_uuid=first_ruleset_uuid,
            name="Человек",
            description="Первая версия",
        ),
        owner_uuid=owner_uuid,
        _session=db_session,
    )
    second_uuid = await controller.insert(
        RaceCreated(
            ruleset_uuid=second_ruleset_uuid,
            name="Человек",
            description="Вторая версия",
        ),
        owner_uuid=owner_uuid,
        _session=db_session,
    )

    assert first_uuid != second_uuid
