"""Название: __init__.py

Путь: backend/db/controller/__init__.py
Автор: stepapetruk@ya.ru
Дата: [05.05.2026]::2026-May-Tuesday
Описание:

Модуль главного контроллера БД.
"""

from backend.db.controller.base import Database
from backend.db.controller.datasheet import DatasheetController
from backend.db.controller.ruleset import RulesetController
from backend.db.controller.token import TokenController
from backend.db.controller.user import UserController


class Database_Controller(Database):
    """Главный контроллер для работты с бд"""

    _user: UserController
    _token: TokenController
    _datasheet: DatasheetController
    _ruleset: RulesetController

    @property
    def User(self) -> UserController:
        """Контроллер для работы с таблицей users"""
        return self._user

    @property
    def Token(self) -> TokenController:
        """Контроллер для работы с таблицей tokens"""
        return self._token

    @property
    def Datasheet(self) -> DatasheetController:
        """Контроллер для работы с таблицей datasheets"""
        return self._datasheet

    @property
    def Rulset(self) -> RulesetController:
        """Контроллер для работы с таблицей rulesets"""
        return self._ruleset

    def __init__(self, url: str) -> None:
        """Инициализирует главный контроллер и все вложенные sub-controller'ы"""
        super().__init__(url)
        self._user = UserController(url)
        self._token = TokenController(url)
        self._datasheet = DatasheetController(url)
        self._ruleset = DatasheetController(url)
