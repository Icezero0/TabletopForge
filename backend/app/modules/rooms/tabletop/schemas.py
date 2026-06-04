from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.rooms.tabletop.constants import DrawingKind


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
