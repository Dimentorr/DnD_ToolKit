"""Название: __init__.py

Путь: backend/api/routers/__init__.py
Автор: stepapetruk@ya.ru
Дата: [04.05.2026]::2026-May-Monday
Описание:

Описание файла.
"""

from backend.api.routers.auth import auth_router
from backend.api.routers.datasheet import datacheet_router
from backend.api.routers.helthcheck import helthcheck_router

__all__ = ["auth_router", "datacheet_router", "helthcheck_router"]
