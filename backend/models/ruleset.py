"""Название: ruleset.py

Путь: backend/models/ruleset.py
Автор: stepapetruk@ya.ru
Дата: [31.05.2026]::2026-May-Sunday
Описание:

Описание файла.
"""

from enum import StrEnum, auto


class Status(StrEnum):
    """Enum возможных статусов состояния для книги правил"""

    InWork = auto()
    Active = auto()
    Archive = auto()
