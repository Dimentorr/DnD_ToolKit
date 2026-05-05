"""Название: dependencies.py

Путь: core/dependencies.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Описание файла.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.db.model.token import TokenData
from backend.db.model.user import User
from core.secuirity import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    """Зависимость, которая извлекает текущего пользователя из токена.

    Используется для защиты эндпоинтов.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # добавить проверку на scope
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_uuid = payload.get("sub")
    if user_uuid is None:
        raise credentials_exception

    token_data = TokenData(user_uuid=user_uuid)

    return token_data
