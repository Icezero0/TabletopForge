from pydantic import BaseModel, ConfigDict


class RoomSettingsPatch(BaseModel):
    pass


class RoomSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_id: int
