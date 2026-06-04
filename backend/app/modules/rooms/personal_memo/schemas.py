from datetime import datetime

from pydantic import BaseModel, Field


class RoomPersonalMemoResponse(BaseModel):
    content: str
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoomPersonalMemoPut(BaseModel):
    content: str = Field(default="", max_length=100_000)
