"""Название: __init__.py

Путь: backend/api/routers/auth/__init__.py
Автор: stepapetruk@ya.ru
Дата: [07.05.2026]::2026-May-Thursday
Описание:

Описание файла.
"""

from backend.api.routers.healthcheck.healthcheck import healthcheck_router

__all__ = ["healthcheck_router"]
