"""Интеграционные тесты частичного обновления рас."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.race import (
    RaceConflictError,
    RaceController,
    RaceNotFoundError,
    RaceValidationError,
)
from backend.db.model.race import RaceUpdated
from tests.helpers import (
    PostgresHarness,
    create_race,
    create_ruleset,
    create_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_update_changes_only_explicit_fields_and_can_clear_parent(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Сохранить непереданные поля и разрешить явный parent_uuid=None."""
    owner_uuid = await create_user(db_session)
    ruleset_uuid = await create_ruleset(db_session, owner_uuid=owner_uuid)
    parent_uuid = await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        name="Родитель",
    )
    child_uuid = await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        parent_uuid=parent_uuid,
        name="Потомок",
    )
    controller = RaceController(postgres.url)

    await controller.update(
        RaceUpdated(uuid=child_uuid, description="Новое описание"),
        owner_uuid=owner_uuid,
        _session=db_session,
    )
    updated = await controller.get(child_uuid, _session=db_session)

    assert updated is not None
    assert updated.name == "Потомок"
    assert updated.parent_uuid == parent_uuid
    assert updated.description == "Новое описание"

    await controller.update(
        RaceUpdated(uuid=child_uuid, parent_uuid=None),
        owner_uuid=owner_uuid,
        _session=db_session,
    )
    without_parent = await controller.get(child_uuid, _session=db_session)

    assert without_parent is not None
    assert without_parent.parent_uuid is None


async def test_update_rejects_duplicate_name(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Преобразовать конфликт уникальности в доменную ошибку."""
    owner_uuid = await create_user(db_session)
    ruleset_uuid = await create_ruleset(db_session, owner_uuid=owner_uuid)
    await create_race(db_session, ruleset_uuid=ruleset_uuid, name="Занято")
    target_uuid = await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        name="Свободно",
    )
    controller = RaceController(postgres.url)

    with pytest.raises(RaceConflictError):
        await controller.update(
            RaceUpdated(uuid=target_uuid, name="Занято"),
            owner_uuid=owner_uuid,
            _session=db_session,
        )


async def test_update_rejects_foreign_race(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Запретить обновление расы из чужой книги правил."""
    owner_uuid = await create_user(db_session, name_prefix="owner")
    intruder_uuid = await create_user(db_session, name_prefix="intruder")
    ruleset_uuid = await create_ruleset(db_session, owner_uuid=owner_uuid)
    race_uuid = await create_race(db_session, ruleset_uuid=ruleset_uuid)
    controller = RaceController(postgres.url)

    with pytest.raises(RaceNotFoundError):
        await controller.update(
            RaceUpdated(uuid=race_uuid, name="Украденное имя"),
            owner_uuid=intruder_uuid,
            _session=db_session,
        )


async def test_update_requires_at_least_one_field(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Отклонить PATCH без изменяемых полей."""
    owner_uuid = await create_user(db_session)
    ruleset_uuid = await create_ruleset(db_session, owner_uuid=owner_uuid)
    race_uuid = await create_race(db_session, ruleset_uuid=ruleset_uuid)
    controller = RaceController(postgres.url)

    with pytest.raises(RaceValidationError):
        await controller.update(
            RaceUpdated(uuid=race_uuid),
            owner_uuid=owner_uuid,
            _session=db_session,
        )
