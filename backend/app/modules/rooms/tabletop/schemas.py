from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.rooms.tabletop.constants import DrawingKind


class RoomCombatant(BaseModel):
    token_id: int
    initiative_bonus: int = 0
    roll: int = Field(ge=1, le=20)
    initiative: int
    turn_order: int = Field(ge=0)
    ready_round: int = Field(default=1, ge=1)


class RoomCombatState(BaseModel):
    active: bool = True
    round: int = Field(default=1, ge=1)
    turn_index: int = Field(default=0, ge=0)
    combatants: list[RoomCombatant] = Field(default_factory=list)


class RoomMusicTrack(BaseModel):
    library_resource_id: int
    asset_id: int
    name: str = Field(min_length=1, max_length=255)


class RoomMusicState(BaseModel):
    tracks: list[RoomMusicTrack] = Field(default_factory=list)
    current_index: int = Field(default=0, ge=0)
    playing: bool = False
    position: float = Field(default=0, ge=0)
    loop_mode: str = Field(default="list", pattern="^(single|list|shuffle)$")
    updated_at: datetime | None = None


class RoomTabletopSettingsResponse(BaseModel):
    grid_cell_ft: float
    grid_cell_px: int
    combat_state: RoomCombatState | None = None
    music_state: RoomMusicState | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomTabletopSettingsPatch(BaseModel):
    grid_cell_ft: float | None = Field(default=None, gt=0)
    grid_cell_px: int | None = Field(default=None, ge=28, le=120)
    combat_state: RoomCombatState | None = None
    music_state: RoomMusicState | None = None


class RoomMapResponse(BaseModel):
    id: int
    room_id: int
    library_resource_id: int
    asset_id: int | None  # from library_resource.primary_asset_id
    x: float
    y: float
    scale: float
    scale_x: float | None = None
    scale_y: float | None = None
    locked: bool
    z_index: int
    map_grid_x: float | None = None  # from library_resource
    map_grid_y: float | None = None  # from library_resource
    map_grid_size: float | None = None  # from library_resource (fitted cell width)
    map_grid_cell_height: float | None = None  # from library_resource (fitted cell height)
    map_grid_calibration: list | None = None  # from library_resource
    resource_name: str | None = None  # from library_resource
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_orm(cls, room_map: Any) -> "RoomMapResponse":
        lr = room_map.library_resource
        return cls(
            id=room_map.id,
            room_id=room_map.room_id,
            library_resource_id=room_map.library_resource_id,
            asset_id=lr.primary_asset_id if lr else None,
            resource_name=lr.name if lr else None,
            x=room_map.x,
            y=room_map.y,
            scale=room_map.scale,
            scale_x=room_map.scale_x,
            scale_y=room_map.scale_y,
            locked=room_map.locked,
            z_index=room_map.z_index,
            map_grid_x=lr.map_grid_x if lr else None,
            map_grid_y=lr.map_grid_y if lr else None,
            map_grid_size=lr.map_grid_size if lr else None,
            map_grid_cell_height=lr.map_grid_cell_height if lr else None,
            map_grid_calibration=lr.map_grid_calibration if lr else None,
            created_at=room_map.created_at,
            updated_at=room_map.updated_at,
        )


class RoomMapFromResourceCreate(BaseModel):
    library_resource_id: int
    x: float = 0.0
    y: float = 0.0
    scale: float = Field(default=1.0, gt=0)


class RoomMapPatch(BaseModel):
    x: float | None = None
    y: float | None = None
    scale: float | None = Field(default=None, gt=0)
    scale_x: float | None = Field(default=None, gt=0)
    scale_y: float | None = Field(default=None, gt=0)
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
    asset_id: int | None = None
    linked_character_id: int
    name: str
    x: float
    y: float
    width: float
    height: float
    rotation: float
    z_index: int
    visible: bool
    locked: bool
    panel: dict[str, Any] | None = None
    owner_user_id: int
    linked_character_owner_id: int | None = None
    character_hidden: bool = False
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
    panel: dict[str, Any] | None = None


class SpawnCharacterTokenRequest(BaseModel):
    x: float | None = None
    y: float | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    token_config_id: int | None = None
