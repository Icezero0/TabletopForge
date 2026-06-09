from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


DiceActorType = Literal["user", "token"]
DiceVisibility = Literal["public", "blind"]


class DiceRollCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_type: DiceActorType = "user"
    actor_token_id: int | None = None
    label: str = Field(default="", max_length=255)
    formula: str = Field(min_length=1, max_length=255)
    visibility: DiceVisibility = "public"


class DiceRollResponse(BaseModel):
    id: int
    room_id: int
    roller_user_id: int
    actor_type: DiceActorType
    actor_token_id: int | None = None
    actor_display_name: str
    label: str
    formula: str
    visibility: DiceVisibility
    total: int | None = None
    detail: dict[str, Any] | None = None
    hidden: bool = False
    created_at: datetime | None = None


class DiceRollListResponse(BaseModel):
    items: list[DiceRollResponse]
    next_before_id: int | None = None
