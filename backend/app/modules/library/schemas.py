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
