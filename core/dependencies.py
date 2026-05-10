"""Название: dependencies.py

Путь: core/dependencies.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Зависимости FastAPI для проверки авторизации пользователя.

Содержит dependency-функции, которые извлекают access-токен из HTTP-only cookie,
проверяют JWT payload и возвращают данные текущего пользователя для защищённых
endpoint'ов.
"""

from typing import Annotated, Callable

from fastapi import Cookie, Depends, HTTPException, status

from backend.models.token import CookieTokenData, UserRole
from core.security import decode_token

AccessTokenCookie = Annotated[
    str | None,
    Cookie(alias="dnd_tool_kit::access_token"),
]


async def get_current_token_data(
    access_token: AccessTokenCookie = None,
) -> CookieTokenData:
    """Получить данные текущего пользователя из access-токена.

    Извлекает access-токен из HTTP-only cookie, декодирует JWT payload,
    проверяет тип токена и достаёт UUID пользователя из поля `sub`.

    Используется как FastAPI dependency для защиты endpoint'ов, которым нужен
    авторизованный пользователь.

    Args:
        access_token (str | None, optional): JWT access-токен из cookie
            `dnd_tool_kit::access_token`. Если cookie отсутствует, значение
            будет None.
            Defaults to None.

    Returns:
        TokenData: Данные токена с UUID текущего пользователя.

    Raises:
        HTTPException: Возникает со статусом 401, если access-токен отсутствует,
            не декодируется, имеет неверный тип, не содержит поле `sub` или
            содержит некорректный UUID пользователя.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if access_token is None:
        raise credentials_exception
    # добавить проверку на scope
    payload = await decode_token(access_token)
    if payload is None:
        raise credentials_exception

    user_uuid = payload.get("sub")
    scope = payload.get("scope")
    token_type = payload.get("type")
    if user_uuid is None or token_type != "access":
        raise credentials_exception

    token_data = CookieTokenData(
        user_uuid=user_uuid,
        role=scope,
        token_type=token_type,
    )

    return token_data


def require_roles(
    allowed_roles: list[UserRole],
) -> Callable:
    """Создать dependency для проверки роли пользователя.

    Args:
        allowed_roles (list[UserRole]): Роли, которым разрешён доступ.

    Returns:
        Callable: FastAPI dependency, возвращающая данные пользователя из токена.

    Raises:
        HTTPException: Возникает со статусом 403, если роль пользователя
            не входит в список разрешённых.
    """

    async def dependency(
        token_data: Annotated[CookieTokenData, Depends(get_current_token_data)],
    ) -> CookieTokenData:
        if token_data.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        return token_data

    return dependency
