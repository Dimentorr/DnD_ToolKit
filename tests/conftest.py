"""Название: conftest.py

Путь: tests/conftest.py
Автор: stepapetruk@ya.ru
Дата: [19.07.2026]::2026-July-Sunday
Описание:

Общие фикстуры тестового набора.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("APP_SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_ALGORITHM", "HS256")

from backend.db.orm import Base  # noqa: E402
from tests.helpers import PostgresHarness  # noqa: E402


def _get_test_database_url() -> str:
    """Получить явно разрешённый URL PostgreSQL для интеграционных тестов."""
    database_url = os.getenv("DND_TEST_DATABASE_URL")
    if database_url:
        return database_url

    if os.getenv("DND_TEST_USE_CONFIGURED_DATABASE") == "1":
        from core.config import settings

        return settings.db.url

    pytest.skip(
        "Для SQL-тестов задайте DND_TEST_DATABASE_URL либо "
        "DND_TEST_USE_CONFIGURED_DATABASE=1. Рабочие таблицы тесты не изменяют."
    )


@pytest_asyncio.fixture(scope="session")
async def postgres() -> AsyncIterator[PostgresHarness]:
    """Создать отдельную схему PostgreSQL на время тестовой сессии."""
    database_url = make_url(_get_test_database_url())
    if database_url.get_backend_name() != "postgresql":
        pytest.fail("Интеграционные тесты поддерживают только PostgreSQL")

    schema_name = f"dnd_toolkit_test_{uuid4().hex}"
    admin_engine = create_async_engine(database_url)
    schema_engine = None

    try:
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))

        schema_url = database_url.update_query_dict({"options": f"-csearch_path={schema_name}"})
        schema_engine = create_async_engine(schema_url)

        async with schema_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        yield PostgresHarness(
            url=schema_url.render_as_string(hide_password=False),
            engine=schema_engine,
        )
    finally:
        if schema_engine is not None:
            await schema_engine.dispose()

        async with admin_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        await admin_engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    postgres: PostgresHarness,
) -> AsyncIterator[AsyncSession]:
    """Открыть транзакцию, автоматически откатываемую после каждого теста."""
    session_maker = async_sessionmaker(
        postgres.engine,
        expire_on_commit=False,
    )

    async with session_maker() as session:
        transaction = await session.begin()
        try:
            yield session
        finally:
            if transaction.is_active:
                await transaction.rollback()
            else:
                await session.rollback()
