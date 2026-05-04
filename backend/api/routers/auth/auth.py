"""Название: auth.py

Путь: backend/api/routers/auth/auth.py
Автор: stepapetruk@ya.ru
Дата: [04.05.2026]::2026-May-Monday
Описание:

Описание файла.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from backend.api.models.base import BaseHTTPResponse

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/login")
async def login(
    response: Response,
    login_form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> BaseHTTPResponse:
    pass


@auth_router.post("/logout")
async def logout():
    pass
