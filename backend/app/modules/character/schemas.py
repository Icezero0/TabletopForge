from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TokenConfigResponse(BaseModel):
    id: int
    character_id: int
    is_primary: bool
    name: str
    asset_id: int | None
    library_resource_id: int | None = None
    panel_initial: dict[str, Any]
    sort_order: int

    model_config = {"from_attributes": True}


class TokenConfigUpsert(BaseModel):
    """Used in create/patch. id=None means create new; id set means update existing."""
    id: int | None = None
    is_primary: bool = False
    name: str = Field(default="", max_length=100)
    asset_id: int | None = None
    library_resource_id: int | None = None
    panel_initial: dict[str, Any] = Field(default_factory=dict)
    sort_order: int = 0


class CharacterStateSummary(BaseModel):
    current_hp: int | None
    max_hp: int | None
    armor_class: int | None
    damage_taken: int | None = None

    model_config = {"from_attributes": True}


class CharacterStateResponse(BaseModel):
    character_id: int
    current_hp: int | None
    max_hp: int | None
    temp_hp: int
    armor_class: int | None
    conditions: dict[str, Any]
    damage_taken: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class CharacterStatePatch(BaseModel):
    current_hp: int | None = None
    max_hp: int | None = None
    temp_hp: int | None = None
    armor_class: int | None = None
    conditions: dict[str, Any] | None = None


class CharacterStateCreate(BaseModel):
    current_hp: int | None = None
    max_hp: int | None = None
    temp_hp: int = 0
    armor_class: int | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)


class CharacterResponse(BaseModel):
    id: int
    owner_id: int
    name: str
    player_name: str
    portrait_asset_id: int | None
    token_image_asset_id: int | None
    system: str
    identity: dict[str, Any]
    flavor: dict[str, Any]
    attributes: dict[str, Any]
    features: dict[str, Any]
    spells: dict[str, Any] | None
    resources: list[dict[str, Any]] = Field(default_factory=list)
    equipment: dict[str, Any]
    extras: dict[str, Any]
    token_configs: list[TokenConfigResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CharacterListResponse(BaseModel):
    items: list[CharacterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CharacterImportPreviewRequest(BaseModel):
    raw_text: str = Field(min_length=1, max_length=50000)


class CharacterImportPreviewResponse(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    player_name: str = Field(default="", max_length=255)
    system: str = Field(default="dnd5e", max_length=50)
    identity: dict[str, Any] = Field(default_factory=dict)
    flavor: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, Any] = Field(default_factory=dict)
    spells: dict[str, Any] | None = None
    resources: list[dict[str, Any]] = Field(default_factory=list)
    equipment: dict[str, Any] = Field(default_factory=dict)
    extras: dict[str, Any] = Field(default_factory=dict)
    state: CharacterStateCreate | None = None


class CharacterCreate(BaseModel):
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
    resources: list[dict[str, Any]] = Field(default_factory=list)
    equipment: dict[str, Any] = Field(default_factory=dict)
    extras: dict[str, Any] = Field(default_factory=dict)
    token_configs: list[TokenConfigUpsert] = Field(default_factory=list)
    state: CharacterStateCreate | None = None


class CharacterPatch(BaseModel):
    """All fields are optional. Only explicitly provided fields are updated.
    For spells and portrait_asset_id, sending null explicitly clears the value."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    player_name: str | None = None
    portrait_asset_id: int | None = None
    token_image_asset_id: int | None = None
    system: str | None = Field(default=None, max_length=50)
    identity: dict[str, Any] | None = None
    flavor: dict[str, Any] | None = None
    attributes: dict[str, Any] | None = None
    features: dict[str, Any] | None = None
    spells: dict[str, Any] | None = None
    resources: list[dict[str, Any]] | None = None
    equipment: dict[str, Any] | None = None
    extras: dict[str, Any] | None = None
    token_configs: list[TokenConfigUpsert] | None = None
