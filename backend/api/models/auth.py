"""Название: auth.py

Путь: backend/api/models/auth.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Модели ответов авторизации.
"""

from backend.api.models.base import BaseHTTPResponse


class LoginForm(BaseHTTPResponse):
    """Модель ответа успешной авторизации."""

    access_token: str
    refresh_token: str
