"""Название: auth.py

Путь: backend/api/routers/auth/auth.py
Автор: stepapetruk@ya.ru
Дата: [04.05.2026]::2026-May-Monday
Описание:

Описание файла.
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.api.models.auth import LoginForm
from backend.api.models.base import BaseHTTPResponse
from backend.db.controller import Database_Controller
from backend.db.model.user import UserCreated
from core.config import settings
from core.secuirity import create_access_token, create_refresh_token, get_password_hash, refresh_tokens, verify_password

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

    hashed_password = get_password_hash(user_data.password)
    # TODO нужна ли соль?
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
    if not user or not verify_password(login_form.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.uuid)})
    refresh_token = create_refresh_token(data={"sub": str(user.uuid)})
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
    # _user_data: Annotated[dict, Depends(get_current_user)],
    request: Request,
    response: Response,
) -> BaseHTTPResponse:
    """Выйти из аккаунта пользователя.

    Удаляет cookie с access token и refresh token из HTTP-ответа.
    После выполнения запроса клиент должен считать текущую пользовательскую
    сессию завершённой.

    Args:
        request: Входящий HTTP-запрос.
        response: HTTP-ответ, из которого удаляются cookie с токенами.

    Returns:
        Базовый HTTP-ответ с сообщением по умолчанию.
    """
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


@auth_router.post(path="/refresh", response_model=LoginForm)
async def refresh(
    response: Response,
    access_token: str = Cookie(default=None, alias="dnd_tool_kit::access_token"),
    refresh_token: str = Cookie(default=None, alias="dnd_tool_kit::refresh_token"),
) -> LoginForm:
    """Обновить пару access/refresh токенов.

    Получает текущие access token и refresh token из cookie, выполняет их
    проверку и создаёт новую пару токенов. Новые токены устанавливаются
    в HTTP-only cookie и возвращаются в теле ответа.

    Args:
        response: HTTP-ответ, в который устанавливаются обновлённые cookie с токенами.
        access_token: Текущий access token из cookie.
        refresh_token: Текущий refresh token из cookie.

    Returns:
        Модель ответа с новым access token и новым refresh token.
    """
    new_access_token, new_refresh_token = await refresh_tokens(
        refresh_token=refresh_token,
        access_token=access_token,
    )

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
