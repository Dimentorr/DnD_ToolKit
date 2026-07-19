"""Тесты ORM-метаданных и ограничений таблиц."""

from typing import Any

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import configure_mappers

from backend.db.orm.datasheets import Datasheet
from backend.db.orm.race import Race
from backend.db.orm.ruleset import Ruleset


def _ondelete(column: Column[Any]) -> str | None:
    """Вернуть действие ON DELETE единственного внешнего ключа столбца."""
    return next(iter(column.foreign_keys)).ondelete


def test_all_relationships_can_be_configured() -> None:
    """Проверить согласованность имён relationship и back_populates."""
    configure_mappers()


def test_race_constraints_are_present() -> None:
    """Зафиксировать ограничения имени, дерева и уникальности расы."""
    constraint_names = {constraint.name for constraint in Race.__table__.constraints if constraint.name is not None}

    assert "ck_races_name_length" in constraint_names
    assert "ck_races_parent_not_self" in constraint_names
    assert "uq_races_ruleset_uuid_name" in constraint_names


def test_foreign_key_delete_actions_match_domain_rules() -> None:
    """Зафиксировать CASCADE и SET NULL для связей таблиц."""
    assert _ondelete(Race.__table__.c.ruleset_uuid) == "CASCADE"
    assert _ondelete(Race.__table__.c.parent_uuid) == "SET NULL"
    assert _ondelete(Datasheet.__table__.c.user_uuid) == "CASCADE"
    assert _ondelete(Datasheet.__table__.c.ruleset_uuid) == "SET NULL"
    assert _ondelete(Datasheet.__table__.c.race_uuid) == "SET NULL"
    assert _ondelete(Ruleset.__table__.c.owner_uuid) == "SET NULL"


def test_database_column_types_are_explicit() -> None:
    """Проверить текстовые и JSONB-типы изменённых таблиц."""
    assert isinstance(Race.__table__.c.description.type, Text)
    assert isinstance(Datasheet.__table__.c.stats.type, JSONB)
    assert isinstance(Datasheet.__table__.c.wallet.type, JSONB)
    assert isinstance(Datasheet.__table__.c.features.type, JSONB)
    assert isinstance(Datasheet.__table__.c.inventory.type, JSONB)
