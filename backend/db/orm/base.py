"""Название: base.py

Путь: backend/db/orm/base.py
Автор: stepapetruk@ya.ru
Дата: [03.05.2026]::2026-May-Sunday
Описание:

Базовая модель для всех orm-моделей в проекте.
"""

from abc import abstractmethod

from sqlalchemy.orm import DeclarativeBase
from backend.models.base import BasePydanticModel


class Base(DeclarativeBase):
    """Base class fro save all ORM model in metadate and work with this"""

    @abstractmethod
    def as_model(self) -> BasePydanticModel:
        """ABC method for each ORM model.

        Convert ORM into pydantic model
        """

    def __str__(self) -> str:
        """Получить строковое предствление объета"""
        return self.as_model().__str__()

    def __repr__(self) -> str:
        """Получить строковое предствление объета для отладки"""
        return self.as_model().__repr__()
