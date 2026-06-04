from hashlib import sha256
from math import ceil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, UnauthorizedError
from app.modules.assets.constants import (
    ALLOWED_AUDIO_CONTENT_TYPES,
    ALLOWED_IMAGE_CONTENT_TYPES,
    DEDUPED_ASSET_TYPES,
    USER_LIBRARY_ASSET_TYPES,
    AssetType,
)
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

    def _extension_for_upload(self, file: UploadFile, asset_type: AssetType) -> str:
        allowed_content_types = {
            AssetType.AVATAR: ALLOWED_IMAGE_CONTENT_TYPES,
            AssetType.FEEDBACK_IMAGE: ALLOWED_IMAGE_CONTENT_TYPES,
            AssetType.MAP_BACKGROUND: ALLOWED_IMAGE_CONTENT_TYPES,
            AssetType.IMAGE: ALLOWED_IMAGE_CONTENT_TYPES,
            AssetType.AUDIO: ALLOWED_AUDIO_CONTENT_TYPES,
        }.get(asset_type)

        if allowed_content_types is None or file.content_type not in allowed_content_types:
            raise BadRequestError(
                "Unsupported asset file type",
                reason=ErrorReason.INVALID_ASSET_FILE,
                details={
                    "asset_type": asset_type,
                    "content_type": file.content_type,
                },
            )
        return allowed_content_types[file.content_type]

    def _asset_type(self, asset: Asset) -> AssetType:
        try:
            return AssetType(asset.asset_type)
        except ValueError as exc:
            raise BadRequestError(
                "Unsupported asset type",
                reason=ErrorReason.INVALID_ASSET_FILE,
                details={"asset_type": asset.asset_type},
            ) from exc

    async def create_upload_asset(
        self,
        db: AsyncSession,
        *,
        file: UploadFile,
        asset_type: AssetType,
        owner_id: int | None,
        feedback_id: int | None = None,
    ) -> Asset:
        extension = self._extension_for_upload(file, asset_type)
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

        content_hash = sha256(content).hexdigest()

        if asset_type in DEDUPED_ASSET_TYPES:
            existing = await self.repo.find_asset_by_fingerprint(
                db,
                asset_type=asset_type.value,
                content_hash=content_hash,
                content_type=file.content_type or "application/octet-stream",
                size_bytes=len(content),
            )
            if existing is not None:
                existing.ref_count += 1
                return await self.repo.save_asset(db, existing)

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
            content_hash=content_hash,
        )

    async def create_user_library_asset(
        self,
        db: AsyncSession,
        *,
        file: UploadFile,
        asset_type: AssetType,
        user: User,
    ) -> Asset:
        if asset_type not in USER_LIBRARY_ASSET_TYPES:
            raise BadRequestError(
                "Unsupported asset type for user library",
                reason=ErrorReason.INVALID_ASSET_FILE,
                details={"asset_type": asset_type},
            )

        asset = await self.create_upload_asset(
            db,
            file=file,
            asset_type=asset_type,
            owner_id=user.id,
        )
        await db.commit()
        await db.refresh(asset)
        return asset

    async def create_image_asset(
        self,
        db: AsyncSession,
        *,
        file: UploadFile,
        asset_type: AssetType,
        owner_id: int | None,
        feedback_id: int | None = None,
    ) -> Asset:
        return await self.create_upload_asset(
            db,
            file=file,
            asset_type=asset_type,
            owner_id=owner_id,
            feedback_id=feedback_id,
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

    async def get_user_library_assets(
        self,
        db: AsyncSession,
        *,
        user: User,
        page: int,
        page_size: int,
        asset_type: AssetType | None = None,
    ) -> dict:
        if asset_type is not None and asset_type not in USER_LIBRARY_ASSET_TYPES:
            raise BadRequestError(
                "Unsupported asset type for user library",
                reason=ErrorReason.INVALID_ASSET_FILE,
                details={"asset_type": asset_type},
            )

        items, total = await self.repo.get_assets(
            db,
            page=page,
            page_size=page_size,
            asset_type=asset_type.value if asset_type else None,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": ceil(total / page_size) if total else 0,
        }

    async def require_asset_access(
        self,
        db: AsyncSession,
        asset: Asset,
        user: User | None,
    ) -> None:
        asset_type = self._asset_type(asset)

        if asset_type == AssetType.AVATAR:
            return

        if asset_type in USER_LIBRARY_ASSET_TYPES:
            return

        if user is None:
            raise UnauthorizedError(
                "Missing authorization token",
                reason=ErrorReason.MISSING_AUTHORIZATION_TOKEN,
            )

        if asset_type == AssetType.MAP_BACKGROUND:
            if await self.tabletop_repo.user_can_read_map_asset(
                db,
                asset_id=asset.id,
                user_id=user.id,
            ):
                return

        if asset_type == AssetType.FEEDBACK_IMAGE:
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

    async def release_user_library_asset_reference(
        self,
        db: AsyncSession,
        *,
        asset_id: int,
        user: User,
    ) -> None:
        asset = await self.get_asset_by_id(db, asset_id)
        if self._asset_type(asset) not in USER_LIBRARY_ASSET_TYPES:
            raise ForbiddenError(
                "You do not have permission to release this asset",
                reason=ErrorReason.ASSET_PERMISSION_DENIED,
                details={"asset_id": asset.id},
            )

        file_path = self.asset_file_path(asset)
        if asset.ref_count > 1:
            asset.ref_count -= 1
            await self.repo.save_asset(db, asset)
            await db.commit()
            return

        await self.repo.delete_asset(db, asset)
        await db.commit()

        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass
