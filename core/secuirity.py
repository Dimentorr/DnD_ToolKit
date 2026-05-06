"""Название: secuirity.py

Путь: core/secuirity.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Модуль функций безопасности.

Содержит функции для хеширования паролей и refresh-токенов,
проверки пользовательских паролей, создания JWT access/refresh-токенов
и декодирования JWT payload.

Пароли хешируются через bcrypt с автоматической генерацией соли.
Refresh-токены хешируются детерминированно через HMAC-SHA256, чтобы их можно
было безопасно хранить в БД и находить по хешу.
"""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить пароль пользователя.

    Сравнивает переданный пользователем пароль с сохранённым bcrypt-хешем.
    Используется при авторизации пользователя.

    Args:
        plain_password (str): Пароль в открытом виде, полученный из формы
            авторизации.
        hashed_password (str): Bcrypt-хеш пароля, сохранённый в БД.

    Returns:
        bool: True, если пароль соответствует хешу. False, если пароль
        не соответствует хешу.
    """
    return pwd_context.verify(plain_password, hashed_password)


async def get_hash(
    obj: str,
    is_static: bool = False,
) -> str:
    """Получить хеш переданного значения.

    В зависимости от параметра `is_static` использует один из двух режимов:

    - при `is_static=False` создаёт bcrypt-хеш с автоматической случайной солью;
    - при `is_static=True` создаёт детерминированный HMAC-SHA256 хеш.

    Bcrypt-режим подходит для паролей, потому что один и тот же пароль каждый
    раз будет давать новый хеш, но сможет быть проверен через `verify_password`.

    HMAC-SHA256 режим подходит для refresh-токенов, потому что один и тот же
    токен должен каждый раз давать один и тот же хеш для поиска записи в БД.

    Args:
        obj (str): Строковое значение, которое нужно захешировать.
        is_static (bool, optional): Признак детерминированного хеширования.
            Если True, используется HMAC-SHA256. Если False, используется
            bcrypt.
            Defaults to False.

    Returns:
        str: Хеш переданного значения.
    """
    if is_static:
        return hmac.new(
            key=settings.app.SECRET_KEY.encode("utf-8"),
            msg=obj.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
    return pwd_context.hash(obj)


async def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Создать JWT access-токен.

    Формирует короткоживущий access-токен для доступа к защищённым endpoint'ам.
    Access-токен не сохраняется в БД и проверяется по подписи, сроку действия
    и типу токена.

    В payload автоматически добавляются:

    - `exp`: дата и время истечения токена;
    - `type`: тип токена со значением `"access"`.

    Args:
        data (dict): Данные, которые нужно добавить в payload токена.
            Обычно содержит `sub` с UUID пользователя и `scope` с ролью или
            областью доступа.
        expires_delta (timedelta | None, optional): Пользовательское время
            жизни токена. Если не передано, используется значение
            `settings.app.ACCESS_TOKEN_EXPIRE_MINUTES`.
            Defaults to None.

    Returns:
        str: Закодированный JWT access-токен.
    """

    to_encode = data.copy()

    expire = datetime.now(tz=UTC) + (
        expires_delta if expires_delta is not None else timedelta(minutes=settings.app.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "type": "access",
    })

    return jwt.encode(
        to_encode,
        settings.app.SECRET_KEY,
        algorithm=settings.app.ALGORITHM,
    )


async def create_refresh_token(data: dict) -> str:
    """Создать JWT refresh-токен.

    Формирует долгоживущий refresh-токен, который используется для выпуска
    новой пары access/refresh-токенов без повторного ввода логина и пароля.

    Refresh-токен должен сохраняться в БД не в открытом виде, а в виде
    детерминированного HMAC-SHA256 хеша.

    В payload автоматически добавляются:

    - `exp`: дата и время истечения токена;
    - `type`: тип токена со значением `"refresh"`.

    Args:
        data (dict): Данные, которые нужно добавить в payload токена.
            Обычно содержит `sub` с UUID пользователя и `scope` с ролью или
            областью доступа.

    Returns:
        str: Закодированный JWT refresh-токен.
    """

    to_encode = data.copy()
    expire = datetime.now(tz=UTC) + timedelta(days=settings.app.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "type": "refresh",
    })

    return jwt.encode(
        to_encode,
        settings.app.SECRET_KEY,
        algorithm=settings.app.ALGORITHM,
    )


async def decode_token(token: str) -> dict:
    """Декодировать JWT-токен.

    Проверяет подпись JWT-токена и пытается получить его payload.
    Если токен невалиден, повреждён, истёк или подписан неверным ключом,
    возвращает None.

    Args:
        token (str): JWT-токен для декодирования.

    Returns:
        dict | None: Payload токена, если декодирование прошло успешно.
        Если токен невалиден, возвращается None.
    """
    try:
        payload = jwt.decode(token, settings.app.SECRET_KEY, algorithms=[settings.app.ALGORITHM])
        return payload
    except JWTError:
        return None


async def refresh_tokens(
    refresh_token: str | None,
) -> tuple[str, str]:
    """Обновить пару JWT access/refresh-токенов.

    Проверяет переданный refresh-токен и, если он валиден, создаёт новую пару
    access/refresh-токенов для того же пользователя.

    Метод выполняет только базовую JWT-проверку:

    - проверяет наличие refresh-токена;
    - декодирует payload;
    - проверяет тип токена;
    - извлекает UUID пользователя из поля `sub`;
    - создаёт новую пару токенов.

    Проверка refresh-токена по БД, проверка `revoked_at`, `expires_at`
    и refresh-token rotation должны выполняться на уровне контроллера токенов
    или сервисного слоя.

    Args:
        refresh_token (str | None): Refresh-токен пользователя. Обычно
            передаётся из HTTP-only cookie.

    Returns:
        tuple[str, str]: Новая пара токенов в формате
        `(new_access_token, new_refresh_token)`.

    Raises:
        HTTPException: Возникает со статусом 401, если refresh-токен отсутствует,
            не декодируется, имеет неверный тип или не содержит обязательное
            поле `sub`.
    """

    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing",
        )

    refresh_token_data = await decode_token(refresh_token)

    if refresh_token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if refresh_token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_uuid = refresh_token_data.get("sub")

    if user_uuid is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing required information",
        )
    # TODO пока что скоуп только 1, потом докрутить нормальнгую ролёвку
    new_access_token = await create_access_token(
        data={
            "sub": str(user_uuid),
            "scope": "user",
            "type": "access",
        }
    )
    new_refresh_token = await create_refresh_token(
        data={
            "sub": str(user_uuid),
            "scope": "user",
            "type": "refresh",
        }
    )

    return new_access_token, new_refresh_token
