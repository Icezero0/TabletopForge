from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CharacterResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    player_name: str
    portrait_asset_id: int | None
    system: str
    identity: dict[str, Any]
    flavor: dict[str, Any]
    attributes: dict[str, Any]
    features: dict[str, Any]
    spells: dict[str, Any] | None
    equipment: dict[str, Any]
    extras: dict[str, Any]
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CharacterListResponse(BaseModel):
    items: list[CharacterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CharacterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    player_name: str = Field(default="", max_length=255)
    system: str = Field(default="dnd5e", max_length=50)
    portrait_asset_id: int | None = None
    identity: dict[str, Any] = Field(default_factory=dict)
    flavor: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, Any] = Field(default_factory=dict)
    spells: dict[str, Any] | None = None
    equipment: dict[str, Any] = Field(default_factory=dict)
    extras: dict[str, Any] = Field(default_factory=dict)


class CharacterPatch(BaseModel):
    """All fields are optional. Only explicitly provided fields are updated.
    For spells and portrait_asset_id, sending null explicitly clears the value."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    player_name: str | None = None
    portrait_asset_id: int | None = None
    system: str | None = Field(default=None, max_length=50)
    identity: dict[str, Any] | None = None
    flavor: dict[str, Any] | None = None
    attributes: dict[str, Any] | None = None
    features: dict[str, Any] | None = None
    spells: dict[str, Any] | None = None
    equipment: dict[str, Any] | None = None
    extras: dict[str, Any] | None = None
