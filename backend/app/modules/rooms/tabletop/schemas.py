from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.rooms.tabletop.constants import DrawingKind, TokenType


class RoomTabletopSettingsResponse(BaseModel):
    grid_cell_ft: float
    grid_cell_px: int
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomTabletopSettingsPatch(BaseModel):
    grid_cell_ft: float | None = Field(default=None, gt=0)
    grid_cell_px: int | None = Field(default=None, ge=28, le=72)


class RoomMapResponse(BaseModel):
    id: int
    room_id: int
    asset_id: int
    x: float
    y: float
    scale: float
    locked: bool
    z_index: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomMapFromAssetCreate(BaseModel):
    asset_id: int


class RoomMapPatch(BaseModel):
    x: float | None = None
    y: float | None = None
    scale: float | None = Field(default=None, gt=0)
    locked: bool | None = None
    z_index: int | None = None


class RoomDrawingResponse(BaseModel):
    id: int
    room_id: int
    kind: DrawingKind
    geometry: dict[str, Any]
    style: dict[str, Any]
    z_index: int
    created_by_user_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomDrawingCreate(BaseModel):
    kind: DrawingKind
    geometry: dict[str, Any]
    style: dict[str, Any] = Field(default_factory=dict)
    z_index: int = 0


class RoomDrawingPatch(BaseModel):
    geometry: dict[str, Any] | None = None
    style: dict[str, Any] | None = None
    z_index: int | None = None


class RoomDrawingsBulkDelete(BaseModel):
    ids: list[int] = Field(min_length=1)


class RoomTabletopSnapshotResponse(BaseModel):
    settings: RoomTabletopSettingsResponse
    maps: list[RoomMapResponse]
    drawings: list[RoomDrawingResponse]
    tokens: list["RoomTokenResponse"]


class TokenStateSummary(BaseModel):
    current_hp: int | None = None
    max_hp: int | None = None
    ac: int | None = None
    pp: int | None = None
    damage_taken: int | None = None


class RoomTokenResponse(BaseModel):
    id: int
    room_id: int
    asset_id: int | None
    linked_character_id: int | None
    name: str
    token_type: TokenType
    x: float
    y: float
    width: float
    height: float
    rotation: float
    z_index: int
    visible: bool
    locked: bool
    owner_user_id: int
    linked_character_owner_id: int | None = None
    state_summary: TokenStateSummary | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomTokenPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    x: float | None = None
    y: float | None = None
    width: float | None = Field(default=None, gt=0)
    height: float | None = Field(default=None, gt=0)
    rotation: float | None = None
    z_index: int | None = None
    visible: bool | None = None
    locked: bool | None = None
    linked_character_id: int | None = None


class SpawnCharacterTokenRequest(BaseModel):
    x: float | None = None
    y: float | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
