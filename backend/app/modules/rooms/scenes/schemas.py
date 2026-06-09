from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RoomSceneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class RoomSceneRename(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class RoomSceneResponse(BaseModel):
    id: int
    room_id: int
    name: str
    is_active: bool
    created_by_user_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomSceneDetailResponse(RoomSceneResponse):
    snapshot: dict[str, Any]
