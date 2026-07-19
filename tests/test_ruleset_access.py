"""Интеграционные тесты CRUD и доступа к книгам правил."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.ruleset import RulesetController
from backend.db.model.ruleset import RulesetCreated, RulesetUpdated
from tests.helpers import (
    PostgresHarness,
    create_ruleset,
    create_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_ruleset_lifecycle(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Проверить создание, частичное обновление и удаление книги правил."""
    owner_uuid = await create_user(db_session)
    controller = RulesetController(postgres.url)
    ruleset_uuid = await controller.insert(
        RulesetCreated(
            owner_uuid=owner_uuid,
            name="Новая книга",
            description="Описание",
        ),
        _session=db_session,
    )

    await controller.update(
        RulesetUpdated(uuid=ruleset_uuid, name="Новое название"),
        owner_uuid=owner_uuid,
        _session=db_session,
    )
    updated = await controller.get(ruleset_uuid, _session=db_session)

    assert updated is not None
    assert updated.name == "Новое название"
    assert updated.description == "Описание"

    await controller.delete(
        ruleset_uuid,
        owner_uuid=owner_uuid,
        _session=db_session,
    )

    assert await controller.get(ruleset_uuid, _session=db_session) is None


async def test_public_ruleset_is_visible_but_private_is_hidden(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Разрешить чтение публичной и скрыть чужую приватную книгу."""
    owner_uuid = await create_user(db_session, name_prefix="owner")
    reader_uuid = await create_user(db_session, name_prefix="reader")
    public_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        is_public=True,
    )
    private_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        is_public=False,
    )
    controller = RulesetController(postgres.url)

    public_ruleset = await controller.get(
        public_uuid,
        owner_uuid=reader_uuid,
        include_public=True,
        _session=db_session,
    )
    private_ruleset = await controller.get(
        private_uuid,
        owner_uuid=reader_uuid,
        include_public=True,
        _session=db_session,
    )

    assert public_ruleset is not None
    assert private_ruleset is None


async def test_foreign_ruleset_cannot_be_changed_or_deleted(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Запретить изменение и удаление чужой книги правил."""
    owner_uuid = await create_user(db_session, name_prefix="owner")
    intruder_uuid = await create_user(db_session, name_prefix="intruder")
    ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        name="Исходное название",
    )
    controller = RulesetController(postgres.url)

    with pytest.raises(ValueError):
        await controller.update(
            RulesetUpdated(uuid=ruleset_uuid, name="Чужое изменение"),
            owner_uuid=intruder_uuid,
            _session=db_session,
        )

    with pytest.raises(ValueError):
        await controller.delete(
            ruleset_uuid,
            owner_uuid=intruder_uuid,
            _session=db_session,
        )

    ruleset = await controller.get(ruleset_uuid, _session=db_session)
    assert ruleset is not None
    assert ruleset.name == "Исходное название"
