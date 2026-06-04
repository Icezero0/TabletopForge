from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, UnauthorizedError
from app.modules.assets.constants import ALLOWED_IMAGE_CONTENT_TYPES, AssetType
from app.modules.assets.models import Asset
from app.modules.assets.repository import AssetRepository
from app.modules.rooms.tabletop.repository import RoomTabletopRepository
from app.modules.site.constants import SitePermission, SiteRole
from app.modules.site.permissions import require_site_permission
from app.modules.users.models import User


class AssetService:
    def __init__(self) -> None:
        self.repo = AssetRepository()
        self.tabletop_repo = RoomTabletopRepository()
        self.settings = get_settings()

    def _site_role(self, user: User) -> SiteRole:
        try:
            return SiteRole(user.site_role)
        except ValueError:
            return SiteRole.USER

    def _extension_for_upload(self, file: UploadFile) -> str:
        if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise BadRequestError(
                "Unsupported image type",
                reason=ErrorReason.INVALID_ASSET_FILE,
                details={"content_type": file.content_type},
            )
        return ALLOWED_IMAGE_CONTENT_TYPES[file.content_type]

    async def create_image_asset(
        self,
        db: AsyncSession,
        *,
        file: UploadFile,
        asset_type: AssetType,
        owner_id: int | None,
        feedback_id: int | None = None,
    ) -> Asset:
        extension = self._extension_for_upload(file)
        content = await file.read()
        if not content:
            raise BadRequestError(
                "Uploaded file is empty",
                reason=ErrorReason.INVALID_ASSET_FILE,
            )
        if len(content) > self.settings.max_asset_upload_bytes:
            raise BadRequestError(
                "Uploaded file is too large",
                reason=ErrorReason.ASSET_FILE_TOO_LARGE,
                details={"max_bytes": self.settings.max_asset_upload_bytes},
            )

        relative_path = Path(asset_type.value) / f"{uuid4().hex}{extension}"
        absolute_path = self.settings.assets_dir_path / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)

        return await self.repo.create_asset(
            db,
            asset_type=asset_type.value,
            owner_id=owner_id,
            feedback_id=feedback_id,
            original_filename=file.filename,
            storage_path=relative_path.as_posix(),
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
        )

    async def get_asset_by_id(self, db: AsyncSession, asset_id: int) -> Asset:
        asset = await self.repo.get_asset_by_id(db, asset_id)
        if asset is None:
            raise NotFoundError(
                "Asset not found",
                reason=ErrorReason.ASSET_NOT_FOUND,
                details={"asset_id": asset_id},
            )
        return asset

    async def require_asset_access(
        self,
        db: AsyncSession,
        asset: Asset,
        user: User | None,
    ) -> None:
        if asset.asset_type == AssetType.AVATAR.value:
            return

        if user is None:
            raise UnauthorizedError(
                "Missing authorization token",
                reason=ErrorReason.MISSING_AUTHORIZATION_TOKEN,
            )

        if asset.asset_type == AssetType.MAP_BACKGROUND.value:
            if await self.tabletop_repo.user_can_read_map_asset(
                db,
                asset_id=asset.id,
                user_id=user.id,
            ):
                return

        if asset.asset_type == AssetType.FEEDBACK_IMAGE.value:
            if asset.owner_id == user.id:
                return
            try:
                require_site_permission(
                    self._site_role(user),
                    SitePermission.VIEW_ALL_FEEDBACK,
                )
                return
            except ForbiddenError:
                pass

        raise ForbiddenError(
            "You do not have permission to access this asset",
            reason=ErrorReason.ASSET_PERMISSION_DENIED,
            details={"asset_id": asset.id},
        )

    def asset_file_path(self, asset: Asset) -> Path:
        return self.settings.assets_dir_path / asset.storage_path
