from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.modules.assets.constants import AssetType


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_type: AssetType
    owner_id: int | None
    feedback_id: int | None
    original_filename: str | None
    content_type: str
    size_bytes: int
    content_hash: str
    ref_count: int
    created_at: datetime

    @computed_field
    @property
    def url(self) -> str:
        return f"/api/v1/assets/{self.id}/content"


class AssetListResponse(BaseModel):
    items: list[AssetResponse] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int
