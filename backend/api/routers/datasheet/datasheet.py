"""Название: datasheet.py

Путь: backend/api/routers/datasheet/datasheet.py
Автор: stepapetruk@ya.ru
Дата: [07.05.2026]::2026-May-Thursday
Описание:

Группа endpoint'ов для работы с листами персонажей.

Содержит маршруты API для создания и дальнейшего управления листами
персонажей. Доступ к endpoint'ам ограничивается через проверку access-токена
и роли текущего авторизованного пользователя.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.models.base import BaseHTTPResponse
from backend.api.models.datasheet import APIDatasheetCreated
from backend.db.controller import Database_Controller
from backend.db.model.datasheet import Datasheet, DatasheetCreated, DatasheetUpdated
from backend.models.token import CookieTokenData, UserRole
from core.config import settings
from core.dependencies import require_roles

datacheet_router = APIRouter(prefix="/datacheet", tags=["datacheet"])


@datacheet_router.post("/create")
async def create_datasheet(
    data: APIDatasheetCreated,
    current_user: Annotated[
        CookieTokenData,
        Depends(
            require_roles(
                [
                    UserRole.USER,
                    UserRole.MODERATOR,
                    UserRole.ADMIN,
                ],
            ),
        ),
    ],
) -> BaseHTTPResponse:
    """Создать лист персонажа для текущего пользователя.

    Проверяет роль авторизованного пользователя через dependency
    `require_roles`, получает UUID пользователя из access-токена и создаёт
    новый лист персонажа в БД.

    UUID владельца листа не принимается из тела запроса. Он берётся из данных
    текущего пользователя, извлечённых из access-токена. Это не позволяет
    клиенту создать лист персонажа от имени другого пользователя.

    Args:
        data (APIDatasheetCreated): Данные листа персонажа, полученные из
            HTTP-запроса. Содержит имя персонажа, расу, характеристики,
            кошелёк, черты и инвентарь.
        current_user (CookieTokenData): Данные текущего авторизованного
            пользователя, извлечённые из access-токена. Dependency также
            проверяет, что роль пользователя входит в список разрешённых:
            `USER`, `MODERATOR` или `ADMIN`.

    Returns:
        BaseHTTPResponse: Базовый HTTP-ответ с UUID созданного листа персонажа
        в поле `message`.
    """
    _cnt = Database_Controller(url=settings.db.url)
    data_datasheet = DatasheetCreated(
        user_uuid=current_user.user_uuid,
        name=data.name,
        ruleset_uuid=data.ruleset_uuid,
        race=data.race,
        stats=data.stats,
        wallet=data.wallet,
        features=data.features,
        inventory=data.inventory,
    )
    try:
        _uuid = await _cnt.Datasheet.insert(data=data_datasheet)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга правил или раса не найдены",
        ) from error

    return BaseHTTPResponse(message=str(_uuid))


@datacheet_router.patch("/patch")
async def update_datasheet(
    data: DatasheetUpdated,
    current_user: Annotated[
        CookieTokenData,
        Depends(
            require_roles(
                [
                    UserRole.USER,
                    UserRole.MODERATOR,
                    UserRole.ADMIN,
                ],
            ),
        ),
    ],
) -> BaseHTTPResponse:
    """Обновить лист персонажа текущего пользователя.

    Получает лист персонажа по UUID из модели `DatasheetUpdated`, проверяет,
    что лист существует и принадлежит текущему авторизованному пользователю.
    Если проверка пройдена, выполняет частичное обновление переданных полей.

    Обновление чужого листа запрещено. На текущем этапе `MODERATOR` и `ADMIN`
    проходят проверку роли, но всё равно должны быть владельцами листа. Если
    для модераторов или администраторов позже потребуется доступ к чужим листам,
    это условие нужно будет расширить отдельной бизнес-логикой.

    Args:
        data (DatasheetUpdated): Данные для обновления листа персонажа.
            Обязательно содержит UUID листа. Остальные поля обновляются только
            при наличии значения.
        current_user (CookieTokenData): Данные текущего авторизованного
            пользователя, извлечённые из access-токена. Dependency также
            проверяет роль пользователя.

    Returns:
        BaseHTTPResponse: Базовый HTTP-ответ при успешном обновлении.

    Raises:
        HTTPException:
            - Возникает со статусом 400, если запрос не содержит полей
              для обновления или ruleset_uuid явно равен null.
            - Возникает со статусом 404, если лист или выбранные связанные
              объекты не найдены либо недоступны пользователю.
    """
    _cnt = Database_Controller(url=settings.db.url)

    if not data.model_fields_set - {"uuid"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не переданы поля для обновления листа персонажа",
        )

    if "ruleset_uuid" in data.model_fields_set and data.ruleset_uuid is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поле ruleset_uuid не может быть null",
        )

    try:
        await _cnt.Datasheet.update(data=data, owner_uuid=current_user.user_uuid)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лист персонажа не найден",
        ) from error

    return BaseHTTPResponse()


@datacheet_router.get("/get")
async def get_datasheet(
    uuid: UUID,
    current_user: Annotated[
        CookieTokenData,
        Depends(
            require_roles(
                [
                    UserRole.USER,
                    UserRole.MODERATOR,
                    UserRole.ADMIN,
                ],
            ),
        ),
    ],
) -> Datasheet:
    """Получить лист персонажа по UUID.

    Получает лист персонажа из БД по переданному UUID. Endpoint доступен только
    авторизованным пользователям с разрешённой ролью.

    Получение ограничено листами текущего пользователя. Чужой UUID
    возвращает тот же ответ 404, что и отсутствующий лист.

    Args:
        uuid (UUID): UUID листа персонажа, который нужно получить.
        current_user (CookieTokenData): Данные текущего авторизованного
            пользователя, извлечённые из access-токена. Dependency также
            проверяет роль пользователя.

    Returns:
        Datasheet: Данные найденного листа персонажа.

    Raises:
        HTTPException:
            - Возникает со статусом 404, если лист персонажа с
            указанным UUID не найден.
    """
    _cnt = Database_Controller(url=settings.db.url)
    result = await _cnt.Datasheet.get(
        sheet_uuid=uuid,
        owner_uuid=current_user.user_uuid,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лист персонажа не найден",
        )
    return result


@datacheet_router.delete("/delete")
async def delete_datasheet(
    uuid: UUID,
    current_user: Annotated[
        CookieTokenData,
        Depends(
            require_roles(
                [
                    UserRole.USER,
                    UserRole.MODERATOR,
                    UserRole.ADMIN,
                ],
            ),
        ),
    ],
) -> BaseHTTPResponse:
    """Удалить лист персонажа текущего пользователя.

    Получает лист персонажа по UUID, проверяет его существование и принадлежность
    текущему авторизованному пользователю. Если лист найден и принадлежит
    текущему пользователю, выполняет удаление записи из БД.

    Удаление чужого листа запрещено. На текущем этапе `MODERATOR` и `ADMIN`
    проходят проверку роли, но всё равно должны быть владельцами листа. Если
    позже потребуется разрешить администраторам удалять чужие листы, условие
    проверки владельца нужно будет расширить.

    Args:
        uuid (UUID): UUID листа персонажа, который нужно удалить.
        current_user (CookieTokenData): Данные текущего авторизованного
            пользователя, извлечённые из access-токена. Dependency также
            проверяет роль пользователя.

    Returns:
        BaseHTTPResponse: Базовый HTTP-ответ при успешном удалении.

    Raises:
        HTTPException:
            - Возникает со статусом 404, если лист не найден
              или недоступен текущему пользователю.
    """
    _cnt = Database_Controller(url=settings.db.url)

    try:
        await _cnt.Datasheet.delete(
            sheet_uuid=uuid,
            owner_uuid=current_user.user_uuid,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лист персонажа не найден",
        ) from error

    return BaseHTTPResponse()
