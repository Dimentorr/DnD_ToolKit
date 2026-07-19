"""Интеграционные тесты целостности дерева рас."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.controller.race import RaceController, RaceValidationError
from backend.db.model.race import RaceUpdated
from tests.helpers import (
    PostgresHarness,
    create_race,
    create_ruleset,
    create_user,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_race_cannot_be_its_own_parent(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Запретить прямую ссылку parent_uuid на саму расу."""
    owner_uuid = await create_user(db_session)
    ruleset_uuid = await create_ruleset(db_session, owner_uuid=owner_uuid)
    race_uuid = await create_race(db_session, ruleset_uuid=ruleset_uuid)
    controller = RaceController(postgres.url)

    with pytest.raises(RaceValidationError):
        await controller.update(
            RaceUpdated(uuid=race_uuid, parent_uuid=race_uuid),
            owner_uuid=owner_uuid,
            _session=db_session,
        )


async def test_race_tree_cannot_contain_indirect_cycle(
    db_session: AsyncSession,
    postgres: PostgresHarness,
) -> None:
    """Запретить цикл A -> B -> C -> A."""
    owner_uuid = await create_user(db_session)
    ruleset_uuid = await create_ruleset(db_session, owner_uuid=owner_uuid)
    race_a_uuid = await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        name="A",
    )
    race_b_uuid = await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        parent_uuid=race_a_uuid,
        name="B",
    )
    race_c_uuid = await create_race(
        db_session,
        ruleset_uuid=ruleset_uuid,
        parent_uuid=race_b_uuid,
        name="C",
    )
    controller = RaceController(postgres.url)

    with pytest.raises(RaceValidationError):
        await controller.update(
            RaceUpdated(uuid=race_a_uuid, parent_uuid=race_c_uuid),
            owner_uuid=owner_uuid,
            _session=db_session,
        )
