"""Название: base.py

Путь: backend/db/controller/base.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Модуль с базовыми классами взаимодействования с БД.
"""

import datetime
import re
from abc import ABC, ABCMeta
from contextlib import asynccontextmanager
from typing import Self

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from core.config import settings


class Database_Connection_SingletonMeta(ABCMeta):
    """Metaclass implementing the Singleton pattern for classes using this metaclass.

    Inherits from ABCMeta to ensure compatibility with abstract base classes.
    """

    _instances: dict = {}

    def __call__(cls, *args, **kwargs) -> object:
        """Create a singleton instance of the class or returns an existing one."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Database_Connection_SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Database_Connection(ABC, metaclass=Database_Connection_SingletonMeta):
    """Abstract database connection class implementing Singleton pattern.

    Uses SQLAlchemy AsyncEngine and AsyncSession for asynchronous database operations.
    """

    _async_eng: AsyncEngine
    _async_session_maker: async_sessionmaker[AsyncSession]

    def __init__(self, url: str) -> None:
        """Init the database connection with the given URL.

        Creates an async engine and session maker.

        Args:
            url (`str`):
                DB_URL for connection to database
        """
        self._async_eng = create_async_engine(url)
        self._async_session_maker = async_sessionmaker(bind=self._async_eng)

    @property
    def session_maker_async(self) -> AsyncSession:
        """Property that returns a new asynchronous session for database operations."""
        return self._async_session_maker()


class Database(Database_Connection):
    """Database controller."""

    @classmethod
    def build(
        cls,
        url: str = settings.db.url,
    ) -> Self:
        """Create and return a new Database instance using the given URL.

        Supports inheritance

        Args:
            url (`str`, optional):
                The database connection URL.
                ::Defaults to settings.db.url.

        Returns:
            `Database`: A new instance of the Database class.
        """
        # print(settings.db.url)
        return cls(url)

    async def create_db(self) -> None:
        """Create all database tables defined in SQLAlchemy metadata.

        Imports the declarative base metadata and creates all missing tables
        using the current asynchronous engine connection.

        Returns:
            `None`:
                The method does not return a value.
        """
        from backend.db.orm.base import Base

        async with self._async_eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(
        self,
        session: AsyncSession | None = None,
    ) -> AsyncSession:
        """Асинхронный контекстный менеджер для работы с сессиями

        Если сессия не была передана открывает новую.

        Если была передана работает с ней.
        """
        if session is None:
            async with self.session_maker_async as session:
                async with session.begin():
                    yield session
        else:
            yield session

    def parse_datetime(self, value: object) -> datetime.datetime:
        """Привести значение из БД к datetime."""

        if isinstance(value, datetime.datetime):
            return value

        if isinstance(value, str):
            normalized_value = re.sub(
                r"([+-]\d{2})$",
                r"\1:00",
                value,
            )
            return datetime.datetime.fromisoformat(normalized_value)

        raise TypeError(f"Expected datetime or str, got {type(value).__name__}")
