from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.library.constants import ResourceType


class LibraryResourceResponse(BaseModel):
    id: int
    owner_id: int
    type: ResourceType
    name: str
    primary_asset_id: int | None
    meta: dict[str, Any]
    usage_count: int
    created_at: datetime
    updated_at: datetime | None
    map_grid_x: float | None = None
    map_grid_y: float | None = None
    map_grid_size: float | None = None
    map_grid_cell_height: float | None = None
    map_grid_calibration: list[dict[str, float]] | None = None

    model_config = {"from_attributes": True}


class LibraryResourceListResponse(BaseModel):
    items: list[LibraryResourceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LibraryResourcePatch(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    tags: list[str] | None = None
    comment: str | None = None


class LibraryResourceGridPatch(BaseModel):
    map_grid_x: float | None = None
    map_grid_y: float | None = None
    map_grid_size: float | None = Field(default=None, gt=0)
    map_grid_cell_height: float | None = Field(default=None, gt=0)
    map_grid_calibration: list[dict[str, float]] | None = None
