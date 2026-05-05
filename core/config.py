"""Название: config.py

Путь: core/config.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Модуль настроек проекта.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class APPSettings(BaseSettings):
    """Класс настроек fastapi приложения"""

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_prefix="app_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class DBSettings(BaseSettings):
    """Общий класс настроек базы данных"""

    url: str = "postgresql+psycopg://user:password@host:5432/database"
    model_config = SettingsConfigDict(
        env_prefix="database_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class Settings:
    """Общий класс настроек проекта"""

    app: APPSettings = APPSettings()
    db: DBSettings = DBSettings()


settings = Settings()
