# DnD_ToolKit

**DnD_ToolKit** — backend-сервис для мастеров и игроков Dungeons & Dragons.

Проект задуман как API-платформа для ведения кампаний, персонажей и пользовательского игрового контента: листов персонажей, предметов, заклинаний, существ, бросков кубов и вспомогательных инструментов для мастера.

> Статус проекта: early development. Основная архитектура и базовые backend-механики находятся в активной разработке.

---

## Возможности

На текущем этапе проект фокусируется на backend API и базовых доменных сущностях.

### Уже реализуется

- регистрация пользователей;
- авторизация через login/password;
- выпуск access token и refresh token;
- хранение refresh token в БД в виде хеша;
- работа с HTTP-only cookie;
- refresh/logout flow;
- базовая структура FastAPI-приложения;
- подключение PostgreSQL через SQLAlchemy async;
- миграции через Alembic;
- проверка кода через Ruff в GitHub Actions.

### Планируется

- создание и управление кампаниями;
- создание и редактирование листов персонажей;
- пользовательские предметы;
- пользовательские заклинания;
- пользовательские существа / монстры;
- публичный и приватный игровой контент;
- роли пользователей;
- броски кубов и проверки характеристик;
- загрузка файлов, например портретов персонажей;
- расширение API для будущего frontend или Telegram-бота.

---

## Технологический стек

- **Python 3.12+**
- **FastAPI**
- **SQLAlchemy 2.x async**
- **PostgreSQL**
- **Alembic**
- **Pydantic v2**
- **pydantic-settings**
- **Uvicorn**
- **python-jose**
- **passlib / bcrypt**
- **Poetry**
- **Ruff**
- **GitHub Actions**

---

## Структура проекта

```text
DnD_ToolKit/
├── .github/
│   └── workflows/          # CI-пайплайны
├── alembic/                # миграции БД
├── backend/
│   ├── api/                # FastAPI application, routers, response models
│   ├── db/                 # DB controllers, ORM models, DB schemas
│   └── models/             # общие Pydantic-модели
├── core/
│   ├── config.py           # настройки приложения
│   ├── dependencies.py     # FastAPI dependencies
│   └── security.py         # JWT, хеширование, security helpers
├── alembic.ini
├── pyproject.toml
├── poetry.lock
└── README.md