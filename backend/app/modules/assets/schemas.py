from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

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
    created_at: datetime

    @computed_field
    @property
    def url(self) -> str:
        return f"/api/v1/assets/{self.id}/content"
