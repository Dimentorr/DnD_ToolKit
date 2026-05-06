"""Название: base.py

Путь: backend/api/models/base.py
Автор: stepapetruk@ya.ru
Дата: [04.05.2026]::2026-May-Monday
Описание:

Описание файла.
"""

from pydantic import BaseModel


class BaseHTTPResponse(BaseModel):
    """Базовая модель ответа"""

    status_code: str = 200
    message: str = "OK"


class BaseHTTPRequest(BaseModel):
    """Базовая модель запроса"""

    pass
