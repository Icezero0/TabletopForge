from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PresenceState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_id: int
    present_user_ids: list[int]

class RoomSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_id: int
    present_user_ids: list[int]
