"""Название: race.py

Путь: backend/api/routers/race/race.py
Автор: stepapetruk@ya.ru
Дата: [19.07.2026]::2026-July-Sunday
Описание:

Группа endpoint'ов для работы с расами персонажей.

Содержит маршруты API для создания, получения, постраничного получения,
частичного обновления и удаления рас персонажей внутри книг правил.

Доступ к endpoint'ам ограничивается через проверку access-токена и роли
текущего авторизованного пользователя. Операции изменения доступны только
для рас, относящихся к книгам правил текущего пользователя. Операции чтения
учитывают как собственные книги правил пользователя, так и публичные книги
правил других пользователей.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.models.base import BaseHTTPResponse
from backend.api.models.race import APIRaceCreated
from backend.db.controller import Database_Controller
from backend.db.controller.race import RaceConflictError, RaceNotFoundError, RaceValidationError
from backend.db.model.race import Race, RaceCreated, RaceUpdated
from backend.models.token import CookieTokenData, UserRole
from core.config import settings
from core.dependencies import require_roles

race_router = APIRouter(prefix="/race", tags=["race"])


@race_router.post("/create")
async def create_race(
    data: APIRaceCreated,
    current_user: Annotated[
        CookieTokenData,
        Depends(require_roles([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])),
    ],
) -> BaseHTTPResponse:
    """Создать расу персонажа в книге правил текущего пользователя.

    Проверяет роль авторизованного пользователя через dependency `require_roles`,
    преобразует входную API-модель `APIRaceCreated` во внутреннюю модель
    `RaceCreated` и передаёт данные в контроллер БД.

    Создание выполняется от имени текущего пользователя. UUID владельца не берётся
    из тела запроса: контроллер получает `owner_uuid` из access-токена и проверяет,
    что указанная книга правил принадлежит текущему пользователю.

    Если передан `parent_uuid`, контроллер БД дополнительно проверяет, что
    родительская раса относится к той же книге правил. Название расы должно быть
    уникальным внутри одной книги правил.

    Args:
        data (APIRaceCreated): Данные создаваемой расы. Содержит UUID книги
            правил, опциональный UUID родительской расы, название и описание.
        current_user (CookieTokenData): Данные текущего авторизованного
            пользователя, извлечённые из access-токена. Dependency также
            проверяет, что роль пользователя входит в список разрешённых:
            `USER`, `MODERATOR` или `ADMIN`.

    Returns:
        BaseHTTPResponse: Базовый HTTP-ответ с UUID созданной расы
        в поле `message`.

    Raises:
        HTTPException:
            - Возникает со статусом 404, если книга правил не найдена
            или недоступна текущему пользователю.
            - Возникает со статусом 400, если данные нарушают правила
            доменной валидации.
            - Возникает со статусом 409, если имя расы уже используется
            в указанной книге правил.
    """
    controller = Database_Controller(url=settings.db.url)
    race = RaceCreated(
        ruleset_uuid=data.ruleset_uuid,
        parent_uuid=data.parent_uuid,
        name=data.name,
        description=data.description,
    )

    try:
        race_uuid = await controller.Race.insert(
            data=race,
            owner_uuid=current_user.user_uuid,
        )
    except RaceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга правил не найдена",
        ) from error
    except RaceValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except RaceConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return BaseHTTPResponse(message=str(race_uuid))


@race_router.patch("/patch")
async def update_race(
    data: RaceUpdated,
    current_user: Annotated[
        CookieTokenData,
        Depends(require_roles([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])),
    ],
) -> BaseHTTPResponse:
    """Частично обновить расу персонажа.

    Проверяет, что в запросе передано хотя бы одно поле для обновления, кроме UUID,
    после чего передаёт данные в контроллер БД. UUID используется только для поиска
    расы и не считается обновляемым полем.

    Обновление разрешено только для рас, относящихся к книгам правил текущего
    пользователя. На текущем этапе роли `MODERATOR` и `ADMIN` проходят проверку
    доступа к endpoint'у, но не получают дополнительных прав на изменение чужих
    книг правил.

    При изменении `parent_uuid` контроллер БД проверяет, что новая родительская
    раса относится к той же книге правил и что новая связь не создаёт цикл
    в иерархии рас.

    Args:
        data (RaceUpdated): Данные для частичного обновления расы. Обязательно
            содержит UUID расы. Остальные поля обновляются только при явной
            передаче в запросе.
        current_user (CookieTokenData): Данные текущего авторизованного
            пользователя, извлечённые из access-токена. Dependency также
            проверяет роль пользователя.

    Returns:
        BaseHTTPResponse: Базовый HTTP-ответ при успешном обновлении.

    Raises:
        HTTPException:
            - Возникает со статусом 400, если не передано ни одного поля
            для обновления или данные нарушают правила доменной валидации.
            - Возникает со статусом 404, если раса не найдена или недоступна
            текущему пользователю.
            - Возникает со статусом 409, если обновление приводит к конфликту,
            например к повтору имени внутри одной книги правил.
    """
    if not data.model_fields_set - {"uuid"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не переданы поля для обновления расы",
        )

    controller = Database_Controller(url=settings.db.url)
    try:
        await controller.Race.update(
            data=data,
            owner_uuid=current_user.user_uuid,
        )
    except RaceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Раса не найдена",
        ) from error
    except RaceValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except RaceConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return BaseHTTPResponse()


@race_router.get("/get")
async def get_race(
    uuid: UUID,
    current_user: Annotated[
        CookieTokenData,
        Depends(require_roles([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])),
    ],
) -> Race:
    """Получить расу персонажа по UUID.

    Получает расу из БД по переданному UUID с учётом прав текущего пользователя.
    Endpoint возвращает расу, если она относится к книге правил текущего
    пользователя или находится в публичной книге правил другого пользователя.

    Приватные расы из чужих книг правил не раскрываются. Для клиента такой случай
    возвращается как 404, чтобы не сообщать о существовании приватной сущности.

    Args:
        uuid (UUID): UUID расы, которую необходимо получить.
        current_user (CookieTokenData): Данные текущего авторизованного
            пользователя, извлечённые из access-токена. Dependency также
            проверяет роль пользователя.

    Returns:
        Race: Данные найденной расы.

    Raises:
        HTTPException:
            - Возникает со статусом 404, если раса не найдена или недоступна
            текущему пользователю.
    """
    controller = Database_Controller(url=settings.db.url)
    race = await controller.Race.get(
        race_uuid=uuid,
        owner_uuid=current_user.user_uuid,
        include_public=True,
    )
    if race is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Раса не найдена",
        )
    return race


@race_router.get("/list")
async def list_races(
    ruleset_uuid: UUID,
    current_user: Annotated[
        CookieTokenData,
        Depends(require_roles([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])),
    ],
    cursor: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[Race]:
    """Получить страницу рас из книги правил.

    Возвращает список рас, относящихся к указанной книге правил, с учётом прав
    текущего пользователя. Доступ разрешён, если книга правил принадлежит текущему
    пользователю или является публичной.

    Для постраничной выдачи используется cursor-пагинация. Параметр `cursor`
    передаётся в контроллер БД как внешний курсор следующей страницы. Параметр
    `limit` ограничивает размер страницы и валидируется FastAPI: допустимые
    значения находятся в диапазоне от 1 до 100 включительно.

    Args:
        ruleset_uuid (UUID): UUID книги правил, для которой необходимо получить
            список рас.
        current_user (CookieTokenData): Данные текущего авторизованного
            пользователя, извлечённые из access-токена. Dependency также
            проверяет роль пользователя.
        cursor (UUID | None): Курсор страницы. Если не передан, возвращается
            первая страница.
        limit (int): Максимальное количество рас в ответе. Значение должно быть
            от 1 до 100 включительно.

    Returns:
        list[Race]: Список рас, доступных текущему пользователю в рамках указанной
        книги правил.

    Raises:
        HTTPException:
            - Возникает со статусом 404, если книга правил не найдена
            или недоступна текущему пользователю.
    """
    controller = Database_Controller(url=settings.db.url)
    try:
        return await controller.Race.list_by_ruleset(
            ruleset_uuid=ruleset_uuid,
            owner_uuid=current_user.user_uuid,
            include_public=True,
            cursor=cursor,
            limit=limit,
        )
    except RaceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга правил не найдена",
        ) from error


@race_router.delete("/delete")
async def delete_race(
    uuid: UUID,
    current_user: Annotated[
        CookieTokenData,
        Depends(require_roles([UserRole.USER, UserRole.MODERATOR, UserRole.ADMIN])),
    ],
) -> BaseHTTPResponse:
    """Удалить расу персонажа.

    Удаляет расу по UUID с учётом прав текущего пользователя. Удаление разрешено
    только для рас, относящихся к книгам правил текущего пользователя.

    На текущем этапе роли `MODERATOR` и `ADMIN` проходят проверку доступа
    к endpoint'у, но не получают дополнительных прав на удаление чужих рас.
    Если позднее потребуется административное удаление, проверку владельца
    нужно будет расширить отдельной бизнес-логикой.

    Args:
        uuid (UUID): UUID расы, которую необходимо удалить.
        current_user (CookieTokenData): Данные текущего авторизованного
            пользователя, извлечённые из access-токена. Dependency также
            проверяет роль пользователя.

    Returns:
        BaseHTTPResponse: Базовый HTTP-ответ при успешном удалении.

    Raises:
        HTTPException:
            - Возникает со статусом 404, если раса не найдена или недоступна
            текущему пользователю.
    """
    controller = Database_Controller(url=settings.db.url)
    try:
        await controller.Race.delete(
            race_uuid=uuid,
            owner_uuid=current_user.user_uuid,
        )
    except RaceNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Раса не найдена",
        ) from error

    return BaseHTTPResponse()
