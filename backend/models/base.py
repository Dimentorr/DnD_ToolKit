"""Название: base.py

Путь: backend/models/base.py
Автор: stepapetruk@ya.ru
Дата: [03.05.2026]::2026-May-Sunday
Описание:

Базовая модель для всех pydantic-моделей в проекте.
"""

from pydantic import BaseModel


class BasePydanticModel(BaseModel):
    """My BaseModel for all pydantic model"""

    def __str__(self) -> str:
        """Получить строковое предствление объета"""
        class_name = self.__class__.__name__
        data = self.model_dump()
        first_field = next(iter(data.items()), None)
        if first_field:
            key, value = first_field
            return f"{class_name}({key}={value!r})"
        return f"{class_name}()"

    def __repr__(self) -> str:
        """Получить строковое предствление объета для отладки"""
        class_name = self.__class__.__name__
        data = self.model_dump()
        fields_str = ", ".join(f"{k}={v!r}" for k, v in data.items())
        return f"{class_name}({fields_str})"
