from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.assets.service import AssetService
from app.modules.auth.deps import get_optional_current_user
from app.modules.users.models import User

router = APIRouter(prefix="/assets", tags=["assets"])

asset_service = AssetService()


@router.get("/{asset_id}/content")
async def get_asset_content(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> FileResponse:
    asset = await asset_service.get_asset_by_id(db, asset_id)
    asset_service.require_asset_access(asset, current_user)
    return FileResponse(
        asset_service.asset_file_path(asset),
        media_type=asset.content_type,
        filename=asset.original_filename,
        content_disposition_type="inline",
    )
