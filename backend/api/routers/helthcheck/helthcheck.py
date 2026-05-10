"""Название: helthcheck.py

Путь: backend/api/routers/helthcheck/helthcheck.py
Автор: stepapetruk@ya.ru
Дата: [10.05.2026]::2026-May-Sunday
Описание:

Модуль для проверки доступности API.
"""

from fastapi import APIRouter

from backend.api.models.base import BaseHTTPResponse

helthcheck_router = APIRouter(prefix="/helthcheck", tags=["helthcheck"])


@helthcheck_router.get("/check")
async def register():
    """Проверить доступность API.

    Returns:
        Объект базового HTTP-ответа.
    """
    return BaseHTTPResponse()
