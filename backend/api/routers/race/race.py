"""CRUD endpoints for character races."""

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
    """Create a race inside a ruleset owned by the current user."""
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
    """Update selected fields of a race owned through its ruleset."""
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
    """Return an owned race or a race from a public ruleset."""
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
    """Return a cursor-paginated page of visible races."""
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
    """Delete a race owned through its ruleset."""
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
