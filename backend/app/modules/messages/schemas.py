from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.users.schemas import UserResponse


class TextSegmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text"] = "text"
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if value == "":
            raise ValueError("text segment cannot be empty")
        return value


MessageSegmentIn = TextSegmentIn


class MessageContentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segments: list[MessageSegmentIn]

    @field_validator("segments")
    @classmethod
    def validate_segments(cls, value: list[MessageSegmentIn]) -> list[MessageSegmentIn]:
        if not value:
            raise ValueError("segments cannot be empty")
        return value


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: MessageContentIn


# ===== response =====


class TextSegmentOut(BaseModel):
    type: Literal["text"] = "text"
    text: str


MessageSegmentOut = TextSegmentOut


class MessageContentOut(BaseModel):
    segments: list[MessageSegmentOut]


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    sender_user_id: int | None
    sender: UserResponse | None = None
    content: MessageContentOut
    created_at: datetime
    updated_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    next_before_id: int | None = None
