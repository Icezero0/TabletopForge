from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi import Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.assets.constants import AssetType
from app.modules.assets.schemas import AssetListResponse, AssetResponse
from app.modules.assets.service import AssetService
from app.modules.auth.deps import get_current_user, get_optional_current_user
from app.modules.users.models import User

router = APIRouter(prefix="/assets", tags=["assets"])

asset_service = AssetService()


@router.post("", response_model=AssetResponse)
async def create_asset(
    asset_type: AssetType = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssetResponse:
    asset = await asset_service.create_user_library_asset(
        db,
        file=file,
        asset_type=asset_type,
        user=current_user,
    )
    return AssetResponse.model_validate(asset)


@router.get("", response_model=AssetListResponse)
async def get_assets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    asset_type: AssetType | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssetListResponse:
    data = await asset_service.get_user_library_assets(
        db,
        user=current_user,
        page=page,
        page_size=page_size,
        asset_type=asset_type,
    )
    return AssetListResponse(
        items=[AssetResponse.model_validate(asset) for asset in data["items"]],
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
        total_pages=data["total_pages"],
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> AssetResponse:
    asset = await asset_service.get_asset_by_id(db, asset_id)
    await asset_service.require_asset_access(db, asset, current_user)
    return AssetResponse.model_validate(asset)


@router.get("/{asset_id}/content")
async def get_asset_content(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> FileResponse:
    asset = await asset_service.get_asset_by_id(db, asset_id)
    await asset_service.require_asset_access(db, asset, current_user)
    return FileResponse(
        asset_service.asset_file_path(asset),
        media_type=asset.content_type,
        filename=asset.original_filename,
        content_disposition_type="inline",
    )


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    await asset_service.release_user_library_asset_reference(
        db,
        asset_id=asset_id,
        user=current_user,
    )
    return Response(status_code=204)
