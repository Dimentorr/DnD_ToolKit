"""Название: secuirity.py

Путь: core/secuirity.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Модуль с jwt.
"""

from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хэширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Создание access токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.app.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.app.SECRET_KEY, algorithm=settings.app.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Создание refresh токена"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.app.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.app.SECRET_KEY, algorithm=settings.app.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Декодирование токена"""
    try:
        payload = jwt.decode(token, settings.app.SECRET_KEY, algorithms=[settings.app.ALGORITHM])
        return payload
    except JWTError:
        return None


async def refresh_tokens(
    refresh_token: str | None,
    access_token: str | None,
) -> tuple[str, str]:
    """Обновить пару токенов по refresh-токену.

    Args:
        refresh_token (str | None): Refresh-токен из cookie.
        access_token (str | None): Access-токен из cookie (на будущее для БД, сейчас не используется).

    Returns:
        tuple[str, str]: Пара (new_access_token, new_refresh_token).
    """
    if refresh_token is None:
        # TODO сделать нормальные ошибки
        raise ValueError(message="Refresh token is None")

    try:
        refresh_token_data = decode_token(refresh_token)
    except Exception as ex:
        # TODO сделать нормальные ошибки
        raise ValueError(message="Token dont decode") from ex

    user_uuid: str = refresh_token_data.get("sub", None)
    if user_uuid is None:
        # TODO сделать нормальные ошибки
        raise ValueError(message="Refresh token is missing required information")

    new_access_token = create_access_token(data={"sub": str(user_uuid)})
    new_refresh_token = create_refresh_token(data={"sub": str(user_uuid)})

    return new_access_token, new_refresh_token
