from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.character.schemas import (
    CharacterStateCreate,
    CharacterStateSummary,
)


class RoomCharacterTokenConfigSummary(BaseModel):
    id: int
    is_primary: bool
    name: str
    asset_id: int | None

    model_config = {"from_attributes": True}


class RoomCharacterEntryResponse(BaseModel):
    room_character_id: int
    character_id: int
    owner_id: int
    name: str
    player_name: str
    token_image_asset_id: int | None
    token_configs: list[RoomCharacterTokenConfigSummary] = Field(default_factory=list)
    state: CharacterStateSummary
    is_hidden: bool = False

    model_config = {"from_attributes": True}


class RoomCharacterLinkRequest(BaseModel):
    character_id: int


class RoomCharacterVisibilityPatch(BaseModel):
    is_hidden: bool


class RoomCharacterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    player_name: str = Field(default="", max_length=255)
    system: str = Field(default="dnd5e", max_length=50)
    portrait_asset_id: int | None = None
    token_image_asset_id: int | None = None
    identity: dict[str, Any] = Field(default_factory=dict)
    flavor: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, Any] = Field(default_factory=dict)
    spells: dict[str, Any] | None = None
    equipment: dict[str, Any] = Field(default_factory=dict)
    extras: dict[str, Any] = Field(default_factory=dict)
    state: CharacterStateCreate | None = None
