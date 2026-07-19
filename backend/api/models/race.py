"""API models for character races."""

from typing import Any
from uuid import UUID

from pydantic import Field

from backend.models.base import BasePydanticModel


class APIRaceCreated(BasePydanticModel):
    """Data accepted by the race creation endpoint."""

    ruleset_uuid: UUID
    parent_uuid: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    description: str

    def as_dict(self) -> dict[str, Any]:
        """Convert the model to a JSON-compatible dictionary."""
        return self.model_dump(mode="json")
