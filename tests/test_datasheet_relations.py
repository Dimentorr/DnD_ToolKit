"""Интеграционные тесты связей листа персонажа."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.datasheet import DatasheetController
from backend.db.controller.race import RaceController
from backend.db.controller.ruleset import RulesetController
from backend.db.model.datasheet import DatasheetCreated, DatasheetUpdated
from tests.helpers import (
    PostgresHarness,
    create_race,
    create_ruleset,
    create_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_datasheet_can_use_race_from_public_ruleset(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Разрешить персонажу расу из доступной публичной книги."""
    ruleset_owner_uuid = await create_user(db_session, name_prefix="author")
    player_uuid = await create_user(db_session, name_prefix="player")
    ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=ruleset_owner_uuid,
        is_public=True,
    )
    race_uuid = await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        name="Гном",
    )
    controller = DatasheetController(postgres.url)

    sheet_uuid = await controller.insert(
        DatasheetCreated(
            user_uuid=player_uuid,
            ruleset_uuid=ruleset_uuid,
            race=race_uuid,
            name="Брин",
        ),
        _session=db_session,
    )
    sheet = await controller.get(
        sheet_uuid,
        owner_uuid=player_uuid,
        _session=db_session,
    )

    assert sheet is not None
    assert sheet.ruleset_uuid == ruleset_uuid
    assert sheet.race == race_uuid


async def test_datasheet_rejects_race_from_another_ruleset(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Запретить связывать лист и расу из разных книг правил."""
    owner_uuid = await create_user(db_session)
    player_uuid = await create_user(db_session, name_prefix="player")
    selected_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        is_public=True,
    )
    other_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=owner_uuid,
        is_public=True,
    )
    foreign_race_uuid = await create_race(
        db_session,
        ruleset_uuid=other_ruleset_uuid,
    )
    controller = DatasheetController(postgres.url)

    with pytest.raises(ValueError):
        await controller.insert(
            DatasheetCreated(
                user_uuid=player_uuid,
                ruleset_uuid=selected_ruleset_uuid,
                race=foreign_race_uuid,
                name="Неверный лист",
            ),
            _session=db_session,
        )


async def test_datasheet_update_validates_ruleset_and_race_together(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Проверить частичное и совместное обновление связанных UUID."""
    player_uuid = await create_user(db_session)
    first_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=player_uuid,
    )
    second_ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=player_uuid,
    )
    first_race_uuid = await create_race(
        db_session,
        ruleset_uuid=first_ruleset_uuid,
    )
    second_race_uuid = await create_race(
        db_session,
        ruleset_uuid=second_ruleset_uuid,
    )
    controller = DatasheetController(postgres.url)
    sheet_uuid = await controller.insert(
        DatasheetCreated(
            user_uuid=player_uuid,
            ruleset_uuid=first_ruleset_uuid,
            race=first_race_uuid,
            name="Исходное имя",
        ),
        _session=db_session,
    )

    await controller.update(
        DatasheetUpdated(uuid=sheet_uuid, name="Новое имя"),
        owner_uuid=player_uuid,
        _session=db_session,
    )

    with pytest.raises(ValueError):
        await controller.update(
            DatasheetUpdated(uuid=sheet_uuid, race=second_race_uuid),
            owner_uuid=player_uuid,
            _session=db_session,
        )

    await controller.update(
        DatasheetUpdated(
            uuid=sheet_uuid,
            ruleset_uuid=second_ruleset_uuid,
            race=second_race_uuid,
        ),
        owner_uuid=player_uuid,
        _session=db_session,
    )
    updated = await controller.get(
        sheet_uuid,
        owner_uuid=player_uuid,
        _session=db_session,
    )

    assert updated is not None
    assert updated.name == "Новое имя"
    assert updated.ruleset_uuid == second_ruleset_uuid
    assert updated.race == second_race_uuid


async def test_foreign_datasheet_is_hidden_and_foreign_keys_use_set_null(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Проверить доступ к листу и поведение FK при удалении расы и книги."""
    player_uuid = await create_user(db_session, name_prefix="player")
    reader_uuid = await create_user(db_session, name_prefix="reader")
    ruleset_uuid = await create_ruleset(
        db_session,
        owner_uuid=player_uuid,
    )
    race_uuid = await create_race(db_session, ruleset_uuid=ruleset_uuid)
    datasheet_controller = DatasheetController(postgres.url)
    sheet_uuid = await datasheet_controller.insert(
        DatasheetCreated(
            user_uuid=player_uuid,
            ruleset_uuid=ruleset_uuid,
            race=race_uuid,
            name="Защищённый лист",
        ),
        _session=db_session,
    )

    assert (
        await datasheet_controller.get(
            sheet_uuid,
            owner_uuid=reader_uuid,
            _session=db_session,
        )
        is None
    )

    await RaceController(postgres.url).delete(
        race_uuid,
        owner_uuid=player_uuid,
        _session=db_session,
    )
    without_race = await datasheet_controller.get(
        sheet_uuid,
        owner_uuid=player_uuid,
        _session=db_session,
    )

    assert without_race is not None
    assert without_race.race is None
    assert without_race.ruleset_uuid == ruleset_uuid

    await RulesetController(postgres.url).delete(
        ruleset_uuid,
        owner_uuid=player_uuid,
        _session=db_session,
    )
    without_ruleset = await datasheet_controller.get(
        sheet_uuid,
        owner_uuid=player_uuid,
        _session=db_session,
    )

    assert without_ruleset is not None
    assert without_ruleset.ruleset_uuid is None
