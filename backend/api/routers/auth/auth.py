"""Название: auth.py

Путь: backend/api/routers/auth/auth.py
Автор: stepapetruk@ya.ru
Дата: [04.05.2026]::2026-May-Monday
Описание:

Модуль API авторизации.
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.models.auth import LoginForm
from backend.api.models.base import BaseHTTPResponse
from backend.db.controller import Database_Controller
from backend.db.model.token import TokenCreated
from backend.db.model.user import UserCreated
from core.config import settings
from core.security import create_access_token, create_refresh_token, get_hash, verify_password

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register")
async def register(user_data: UserCreated):
    """Зарегистрировать нового пользователя.

    Создаёт нового пользователя на основе переданных регистрационных данных.
    Перед сохранением пароль хешируется и заменяет исходное значение в модели.

    Args:
        user_data: Данные создаваемого пользователя.

    Returns:
        Объект базового HTTP-ответа с сообщением об успешном создании пользователя.

    Raises:
        HTTPException: Если пользователь с указанным логином уже существует.
    """
    _cnt = Database_Controller(url=settings.db.url)

    if await _cnt.User.get_user(login=user_data.name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")

    hashed_password = await get_hash(user_data.password)
    user_data.password = hashed_password
    user_uuid = await _cnt.User.insert(data=user_data)
    return BaseHTTPResponse(message=f"Пользователь успешно создан. uuid: {user_uuid}")


@auth_router.post("/login")
async def login(
    response: Response,
    login_form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> LoginForm:
    """Авторизовать пользователя в системе.

    Проверяет переданные логин и пароль. При успешной авторизации создаёт
    access token и refresh token, устанавливает их в HTTP-only cookie и
    возвращает пару токенов в теле ответа.

    Args:
        response: HTTP-ответ, в который устанавливаются cookie с токенами.
        login_form: Данные формы авторизации OAuth2 с логином и паролем пользователя.

    Returns:
        Модель ответа с access token и refresh token.

    Raises:
        HTTPException: Если пользователь не найден или пароль указан неверно.
    """
    _cnt = Database_Controller(url=settings.db.url)
    user = await _cnt.User.get_user(_is_login=True, login=login_form.username)
    if not user or not await verify_password(login_form.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = await create_access_token(
        data={
            "sub": str(user.uuid),
            "scope": "user",
            "type": "refresh",
        },
    )
    refresh_token = await create_refresh_token(
        data={
            "sub": str(user.uuid),
            "scope": "user",
            "type": "refresh",
        },
    )
    await _cnt.Token.insert(
        data=TokenCreated(
            user_uuid=user.uuid,
            token=refresh_token,
        ),
    )
    response.set_cookie(
        "dnd_tool_kit::access_token",
        access_token,
        httponly=True,
        secure=True,
    )
    response.set_cookie(
        "dnd_tool_kit::refresh_token",
        refresh_token,
        httponly=True,
        secure=True,
    )
    return LoginForm(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Annotated[
        str | None,
        Cookie(alias="dnd_tool_kit::refresh_token"),
    ] = None,
) -> BaseHTTPResponse:
    """Выйти из аккаунта пользователя.

    Удаляет cookie с access token и refresh token из HTTP-ответа.
    После выполнения запроса клиент должен считать текущую пользовательскую
    сессию завершённой.

    Args:
        response: HTTP-ответ, из которого удаляются cookie с токенами.
        refresh_token: хранимый в cookie рефреш токен.

    Returns:
        Базовый HTTP-ответ с сообщением по умолчанию.
    """
    _cnt = Database_Controller(url=settings.db.url)
    hash_token = await get_hash(refresh_token, is_static=True)
    if token := await _cnt.Token.get_by_token_hash(hash_token):
        await _cnt.Token.revoke(token.uuid)
        response.delete_cookie(
            "dnd_tool_kit::access_token",
            httponly=True,
            secure=True,
        )
        response.delete_cookie(
            "dnd_tool_kit::refresh_token",
            httponly=True,
            secure=True,
        )
        return BaseHTTPResponse()
    # TODO сделать нормальные ошибки
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@auth_router.post(path="/refresh", response_model=LoginForm)
async def refresh(
    response: Response,
    refresh_token: str = Cookie(default=None, alias="dnd_tool_kit::refresh_token"),
) -> LoginForm:
    """Обновить пару access/refresh токенов.

    Получает текущие access token и refresh token из cookie, выполняет их
    проверку и создаёт новую пару токенов. Новые токены устанавливаются
    в HTTP-only cookie и возвращаются в теле ответа.

    Args:
        response: HTTP-ответ, в который устанавливаются обновлённые cookie с токенами.
        refresh_token: Текущий refresh token из cookie.

    Returns:
        Модель ответа с новым access token и новым refresh token.
    """
    _cnt = Database_Controller(url=settings.db.url)
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not found refresh tokens.",
        )
    new_access_token, new_refresh_token = await _cnt.Token.refresh_tokens(refresh_token=refresh_token)

    response.set_cookie(
        "dnd_tool_kit::access_token",
        new_access_token,
        httponly=True,
        secure=True,
    )
    response.set_cookie(
        "dnd_tool_kit::refresh_token",
        new_refresh_token,
        httponly=True,
        secure=True,
    )
    return LoginForm(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )
