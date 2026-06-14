from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.rooms.dice.schemas import DiceVisibility


DicePresetKind = Literal["folder", "preset"]


class DicePresetBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parent_id: int | None = Field(default=None, ge=1)
    kind: DicePresetKind = "preset"
    formula: str = Field(default="", max_length=255)
    label: str = Field(default="", max_length=255)
    visibility: DiceVisibility = "public"
    sort_order: int = 0

    @model_validator(mode="after")
    def validate_formula(self) -> "DicePresetBase":
        if self.kind == "preset" and not self.formula.strip():
            raise ValueError("Preset formula is required")
        return self


class DicePresetCreate(DicePresetBase):
    model_config = ConfigDict(extra="forbid")


class DicePresetPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    parent_id: int | None = Field(default=None, ge=1)
    kind: DicePresetKind | None = None
    formula: str | None = Field(default=None, max_length=255)
    label: str | None = Field(default=None, max_length=255)
    visibility: DiceVisibility | None = None
    sort_order: int | None = None


class DicePresetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    parent_id: int | None
    kind: DicePresetKind
    name: str
    formula: str
    label: str
    visibility: DiceVisibility
    sort_order: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DicePresetListResponse(BaseModel):
    items: list[DicePresetResponse]
