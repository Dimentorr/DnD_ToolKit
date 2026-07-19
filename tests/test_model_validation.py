"""Тесты граничной Pydantic-валидации."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.api.models.datasheet import APIDatasheetCreated
from backend.api.models.race import APIRaceCreated
from backend.db.model.race import RaceUpdated
from backend.db.model.ruleset import RulesetCreated
from backend.models.datasheet import Item, Stats, Wallet


def test_race_description_cannot_be_empty() -> None:
    """Отклонить пустое описание на API-границе и при PATCH."""
    with pytest.raises(ValidationError):
        APIRaceCreated(
            ruleset_uuid=uuid4(),
            name="Эльф",
            description="",
        )

    with pytest.raises(ValidationError):
        RaceUpdated(
            uuid=uuid4(),
            description="",
        )


def test_datasheet_name_is_required() -> None:
    """Не подставлять неявное имя листа персонажа."""
    with pytest.raises(ValidationError):
        APIDatasheetCreated(ruleset_uuid=uuid4())


def test_numeric_domain_constraints() -> None:
    """Проверить положительные и неотрицательные числовые поля."""
    with pytest.raises(ValidationError):
        Wallet(gold=-1)

    with pytest.raises(ValidationError):
        Stats(strength=0)

    with pytest.raises(ValidationError):
        Item(uuid=uuid4(), count=0)


def test_ruleset_name_cannot_be_empty() -> None:
    """Отклонить пустое название книги правил."""
    with pytest.raises(ValidationError):
        RulesetCreated(name="")


def test_nested_defaults_are_not_shared() -> None:
    """Не разделять изменяемые значения по умолчанию между моделями."""
    first = APIDatasheetCreated(
        name="Первый",
        ruleset_uuid=uuid4(),
    )
    second = APIDatasheetCreated(
        name="Второй",
        ruleset_uuid=uuid4(),
    )

    first.inventory.data.append(Item(uuid=uuid4()))
    first.wallet.gold = 10

    assert second.inventory.data == []
    assert second.wallet.gold == 0
