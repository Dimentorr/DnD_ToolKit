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

    UUID владельца берётся из access-токена, а не из тела запроса.

    Args:
        data (APIRulesetCreated):
            Данные создаваемой книги правил. Содержит UUID родительской
            книги правил, название, описание,
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
        owner_uuid=current_user.user_uuid,
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
            - Возникает со статусом 400, если не переданы поля для обновления.
            - Возникает со статусом 404, если книга не найдена
              или недоступна текущему пользователю.
    """
    _cnt = Database_Controller(url=settings.db.url)

    if not data.model_fields_set - {"uuid"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не переданы поля для обновления книги правил",
        )

    try:
        await _cnt.Ruleset.update(data=data, owner_uuid=current_user.user_uuid)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга правил не найдена",
        ) from error

    return BaseHTTPResponse()


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

    Пользователь может получить собственную книгу либо публичную книгу
    другого пользователя.

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
    result = await _cnt.Ruleset.get(
        ruleset_uuid=uuid,
        owner_uuid=current_user.user_uuid,
        include_public=True,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга правил не найдена",
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
            - Возникает со статусом 404, если книга не найдена
              или недоступна текущему пользователю.
    """
    _cnt = Database_Controller(url=settings.db.url)

    try:
        await _cnt.Ruleset.delete(
            ruleset_uuid=uuid,
            owner_uuid=current_user.user_uuid,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга правил не найдена",
        ) from error

    return BaseHTTPResponse()
