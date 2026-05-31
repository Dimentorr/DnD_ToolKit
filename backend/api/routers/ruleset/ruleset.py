"""Название: ruleset.py

Путь: backend/api/routers/ruleset/ruleset.py
Автор: stepapetruk@ya.ru
Дата: [31.05.2026]::2026-May-Sunday
Описание:

Группа endpoint'ов для работы с книгами правил.

Содержит маршруты API для создания и дальнейшего управления книгами правил.
Доступ к endpoint'ам ограничивается через проверку access-токена и роли
текущего авторизованного пользователя.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.models.base import BaseHTTPResponse
from backend.api.models.ruleset import APIRulesetCreated
from backend.db.controller import Database_Controller
from backend.db.model.ruleset import Ruleset, RulesetCreated, RulesetUpdated
from backend.models.token import CookieTokenData, UserRole
from core.config import settings
from core.dependencies import require_roles

rule_router = APIRouter(prefix="/rule", tags=["ruleset"])


@rule_router.post("/create")
async def create_ruleset(
    data: APIRulesetCreated,
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
    """Создать новую книгу правил.

    Проверяет роль авторизованного пользователя через dependency `require_roles`,
    преобразует входную API-модель `APIRulesetCreated` во внутреннюю модель `RulesetCreated`
    и добавляет новую запись в таблицу `rulesets`.

    В текущей реализации UUID владельца книги правил принимается из тела запроса в поле `owner_uuid`.

    Args:
        data (APIRulesetCreated):
            Данные создаваемой книги правил. Содержит UUID владельца,
            UUID родительской книги правил, название, описание,
            версию, статус и признак публичности.
        current_user (CookieTokenData):
            Данные текущего авторизованного пользователя, извлечённые из access-токена.
            Dependency также проверяет, что роль пользователя входит в список разрешённых:
            `USER`, `MODERATOR` или `ADMIN`.

    Returns:
        BaseHTTPResponse:
            Базовый HTTP-ответ с UUID созданной книги правил в поле `message`.
    """
    _cnt = Database_Controller(url=settings.db.url)
    data_ruleset = RulesetCreated(
        owner_uuid=data.owner_uuid,
        parent_uuid=data.parent_uuid,
        name=data.name,
        description=data.description,
        version=data.version,
        status=data.status,
        is_public=data.is_public,
    )
    _uuid = await _cnt.Ruleset.insert(data=data_ruleset)

    return BaseHTTPResponse(message=str(_uuid))


@rule_router.patch("/patch")
async def update_ruleset(
    data: RulesetUpdated,
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
    """Обновить книгу правил текущего пользователя.

    Получает книгу правил по UUID из модели `RulesetUpdated`,
    проверяет, что запись существует и принадлежит текущему авторизованному пользователю.
    Если проверки пройдены, выполняет частичное обновление переданных полей.

    Изменение чужой книги правил запрещено.
    На текущем этапе пользователи с ролями `MODERATOR` и `ADMIN` проходят проверку роли,
    но не получают дополнительных прав на редактирование чужих записей.

    Args:
        data (RulesetUpdated):
            Данные для частичного обновления книги правил.
            Обязательно содержит UUID книги.
            Остальные поля обновляются только при наличии в запросе.
        current_user (CookieTokenData):
            Данные текущего авторизованного пользователя, извлечённые из access-токена.
            Dependency также проверяет роль пользователя.

    Returns:
        BaseHTTPResponse:
        Ба  зовый HTTP-ответ при успешном обновлении.

        Raises: HTTPException:
            - Возникает со статусом 400, если книга правил с указанным UUID не найдена.
            - Возникает со статусом 405, если книга правил найдена,
              но не принадлежит текущему пользователю.
    """
    _cnt = Database_Controller(url=settings.db.url)
    if result := await _cnt.Ruleset.get(ruleset_uuid=data.uuid):
        if result.owner_uuid == current_user.user_uuid:
            # TODO добавить условие на роли админа и супер админа, когда сделаю ролёвку
            await _cnt.Ruleset.update(data=data)
            return BaseHTTPResponse()
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Not permission",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Incorrect datasheet uuid",
        headers={"WWW-Authenticate": "Bearer"},
    )


@rule_router.get("/get")
async def get_ruleset(
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
) -> Ruleset:
    """Получить книгу правил по UUID.

    Получает книгу правил из БД по переданному UUID.
    Endpoint доступен авторизованным пользователям с разрешённой ролью.

    В текущей реализации метод не проверяет владельца книги правил
    и значение поля `is_public`. Поэтому любой авторизованный пользователь
    с разрешённой ролью может получить любую существующую книгу правил по известному UUID.

    Args:
    uuid (UUID):
        UUID книги правил, которую необходимо получить.
    current_user (CookieTokenData):
        Данные текущего авторизованного пользователя, извлечённые из access-токена.
        Dependency также проверяет роль пользователя.

    Returns:
        Ruleset: Данные найденной книги правил.

    Raises:
        HTTPException:
            - Возникает со статусом 404, если книга правил с указанным UUID не найдена.
    """
    _cnt = Database_Controller(url=settings.db.url)
    result = await _cnt.Ruleset.get(ruleset_uuid=uuid)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ruleset not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result


@rule_router.delete("/delete")
async def delete_ruleset(
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
    """Удалить книгу правил текущего пользователя.

    Получает книгу правил по UUID, проверяет существование записи
    и принадлежность текущему авторизованному пользователю. Если книга правил
    найдена и принадлежит текущему пользователю, удаляет запись из БД.

    Удаление чужой книги правил запрещено.
    На текущем этапе пользователи с ролями `MODERATOR` и `ADMIN`
    проходят проверку роли, но не получают дополнительных прав
    на удаление чужих записей. Если позднее потребуется разрешить
    административное удаление, проверку владельца необходимо расширить
    отдельной бизнес-логикой.

    Args:
        uuid (UUID):
            UUID книги правил, которую необходимо удалить.
        current_user (CookieTokenData):
            Данные текущего авторизованного пользователя,
            извлечённые из access-токена. Dependency также проверяет роль пользователя.

    Returns:
        BaseHTTPResponse: Базовый HTTP-ответ при успешном удалении.

    Raises:
        HTTPException:
            - Возникает со статусом 400, если книга правил с указанным UUID не найдена.
            - Возникает со статусом 405, если книга правил найдена,
              но не принадлежит текущему пользователю.
    """
    _cnt = Database_Controller(url=settings.db.url)
    if result := await _cnt.Ruleset.get(ruleset_uuid=uuid):
        if result.owner_uuid == current_user.user_uuid:
            await _cnt.Ruleset.delete(ruleset_uuid=uuid)
            return BaseHTTPResponse()
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Not permission",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Incorrect ruleset uuid",
        headers={"WWW-Authenticate": "Bearer"},
    )
