"""Название: __init__.py

Путь: backend/api/__init__.py
Автор: stepapetruk@ya.ru
Дата: [02.05.2026]::2026-May-Saturday
Описание:

Модуль для работы с API.
"""

from fastapi import FastAPI

from backend.api.routers import auth_router, datacheet_router, healthcheck_router, race_router, rule_router


def create_app() -> FastAPI:
    """Создаёт и настраивает экземпляр FastAPI-приложения.

    Returns:
        `FastAPI`: Настроенный экземпляр FastAPI-приложения.
    """
    app = FastAPI(
        root_path="/api/v1",
        docs_url="/docs",
        redoc_url="/redoc",
        title="DnDToolKit::Dev",
        version="0.0.1",
    )
    app.include_router(healthcheck_router)
    app.include_router(auth_router)
    app.include_router(datacheet_router)
    app.include_router(rule_router)
    app.include_router(race_router)

    return app
