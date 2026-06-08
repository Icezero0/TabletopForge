from math import ceil

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.modules.assets.constants import AssetType
from app.modules.assets.service import AssetService
from app.modules.library.constants import RESOURCE_TYPE_SPECS, ResourceType
from app.modules.library.models import LibraryResource
from app.modules.library.repository import LibraryRepository
from app.modules.library.schemas import LibraryResourceGridPatch, LibraryResourceListResponse, LibraryResourceResponse
from app.modules.users.models import User


class LibraryService:
    def __init__(self) -> None:
        self.repo = LibraryRepository()
        self.asset_service = AssetService()

    async def _require_owner(self, resource: LibraryResource, user: User) -> None:
        if resource.owner_id != user.id:
            raise ForbiddenError(
                "You do not have permission to access this resource",
                reason=ErrorReason.LIBRARY_RESOURCE_PERMISSION_DENIED,
                details={"resource_id": resource.id},
            )

    async def _get_or_404(self, db: AsyncSession, *, resource_id: int) -> LibraryResource:
        resource = await self.repo.get_by_id(db, resource_id=resource_id)
        if resource is None:
            raise NotFoundError(
                "Library resource not found",
                reason=ErrorReason.LIBRARY_RESOURCE_NOT_FOUND,
                details={"resource_id": resource_id},
            )
        return resource

    async def create_resource(
        self,
        db: AsyncSession,
        *,
        user: User,
        type: ResourceType,
        name: str,
        image: UploadFile | None = None,
        audio: UploadFile | None = None,
        tags: list[str] | None = None,
        comment: str | None = None,
    ) -> LibraryResource:
        spec = RESOURCE_TYPE_SPECS[type]

        if spec.required_image and image is None:
            raise BadRequestError(
                f"Resource type '{type}' requires an image file",
                reason=ErrorReason.LIBRARY_RESOURCE_TYPE_FIELD_REQUIRED,
                details={"type": type, "missing_field": "image"},
            )

        if spec.required_audio and audio is None:
            raise BadRequestError(
                f"Resource type '{type}' requires an audio file",
                reason=ErrorReason.LIBRARY_RESOURCE_TYPE_FIELD_REQUIRED,
                details={"type": type, "missing_field": "audio"},
            )

        primary_asset_id: int | None = None

        if image is not None:
            asset = await self.asset_service.create_upload_asset(
                db,
                file=image,
                asset_type=AssetType.IMAGE,
                owner_id=user.id,
            )
            primary_asset_id = asset.id
        elif audio is not None:
            asset = await self.asset_service.create_upload_asset(
                db,
                file=audio,
                asset_type=AssetType.AUDIO,
                owner_id=user.id,
            )
            primary_asset_id = asset.id

        meta: dict = {}
        if tags is not None:
            meta["tags"] = tags
        if comment is not None:
            meta["comment"] = comment

        resource = await self.repo.create(
            db,
            owner_id=user.id,
            type=type.value,
            name=name,
            primary_asset_id=primary_asset_id,
            meta=meta,
        )
        await db.commit()
        await db.refresh(resource)
        return resource

    async def get_resource(
        self,
        db: AsyncSession,
        *,
        resource_id: int,
        user: User,
    ) -> LibraryResource:
        resource = await self._get_or_404(db, resource_id=resource_id)
        await self._require_owner(resource, user)
        return resource

    async def list_resources(
        self,
        db: AsyncSession,
        *,
        user: User,
        type: ResourceType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> LibraryResourceListResponse:
        offset = (page - 1) * page_size
        items, total = await self.repo.list_by_owner(
            db,
            owner_id=user.id,
            type=type.value if type is not None else None,
            offset=offset,
            limit=page_size,
        )
        return LibraryResourceListResponse(
            items=[LibraryResourceResponse.model_validate(r) for r in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )

    async def update_resource(
        self,
        db: AsyncSession,
        *,
        resource_id: int,
        user: User,
        name: str,
        tags: list[str] | None = None,
        comment: str | None = None,
    ) -> LibraryResource:
        resource = await self._get_or_404(db, resource_id=resource_id)
        await self._require_owner(resource, user)
        meta_patch: dict | None = None
        if tags is not None or comment is not None:
            meta_patch = {}
            if tags is not None:
                meta_patch["tags"] = tags
            if comment is not None:
                meta_patch["comment"] = comment
        updated = await self.repo.update(db, resource=resource, name=name, meta_patch=meta_patch)
        await db.commit()
        return updated

    async def patch_resource_grid(
        self,
        db: AsyncSession,
        *,
        resource_id: int,
        user: User,
        payload: LibraryResourceGridPatch,
    ) -> LibraryResource:
        resource = await self._get_or_404(db, resource_id=resource_id)
        await self._require_owner(resource, user)
        updated = await self.repo.update_grid(
            db,
            resource=resource,
            map_grid_x=payload.map_grid_x,
            map_grid_y=payload.map_grid_y,
            map_grid_size=payload.map_grid_size,
            map_grid_cell_height=payload.map_grid_cell_height,
            map_grid_calibration=payload.map_grid_calibration,
        )
        await db.commit()
        return updated

    async def delete_resource(
        self,
        db: AsyncSession,
        *,
        resource_id: int,
        user: User,
    ) -> None:
        resource = await self._get_or_404(db, resource_id=resource_id)
        await self._require_owner(resource, user)

        if resource.usage_count > 0:
            raise ConflictError(
                "Resource is currently in use on the tabletop and cannot be deleted",
                reason=ErrorReason.LIBRARY_RESOURCE_IN_USE,
                details={"resource_id": resource_id, "usage_count": resource.usage_count},
            )

        primary_asset_id = resource.primary_asset_id
        await self.repo.delete(db, resource=resource)

        if primary_asset_id is not None:
            asset = await self.asset_service.get_asset_by_id(db, primary_asset_id)
            if asset.ref_count > 1:
                asset.ref_count -= 1
            else:
                file_path = self.asset_service.asset_file_path(asset)
                await db.delete(asset)
                await db.flush()
                try:
                    file_path.unlink(missing_ok=True)
                except OSError:
                    pass

        await db.commit()

    # =========================
    # Extension points (not exposed via API yet — consumed by tabletop service)
    # =========================

    async def increment_usage(
        self,
        db: AsyncSession,
        *,
        resource_id: int,
    ) -> None:
        resource = await self._get_or_404(db, resource_id=resource_id)
        await self.repo.adjust_usage_count(db, resource=resource, delta=1)

    async def decrement_usage(
        self,
        db: AsyncSession,
        *,
        resource_id: int,
    ) -> None:
        resource = await self._get_or_404(db, resource_id=resource_id)
        await self.repo.adjust_usage_count(db, resource=resource, delta=-1)

    async def create_resource_from_asset_id(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        type: ResourceType,
        name: str,
        asset_id: int | None = None,
    ) -> LibraryResource:
        """Create a LibraryResource backed by an already-existing asset (no file upload).
        The caller is responsible for committing the transaction.
        If asset_id is provided, its ref_count is incremented to reflect the new reference.
        """
        if asset_id is not None:
            asset = await self.asset_service.get_asset_by_id(db, asset_id)
            asset.ref_count += 1

        resource = await self.repo.create(
            db,
            owner_id=owner_id,
            type=type.value,
            name=name,
            primary_asset_id=asset_id,
            meta={},
        )
        return resource

    async def copy_resource(
        self,
        db: AsyncSession,
        *,
        resource_id: int,
        to_user: User,
    ) -> LibraryResource:
        """Copy a visible resource into to_user's library. Caller is responsible for
        verifying the resource is accessible (e.g. visible on the tabletop)."""
        source = await self._get_or_404(db, resource_id=resource_id)

        if source.primary_asset_id is not None:
            asset = await self.asset_service.get_asset_by_id(db, source.primary_asset_id)
            asset.ref_count += 1

        new_resource = await self.repo.create(
            db,
            owner_id=to_user.id,
            type=source.type,
            name=source.name,
            primary_asset_id=source.primary_asset_id,
            meta=dict(source.meta),
        )
        await db.commit()
        await db.refresh(new_resource)
        return new_resource

    async def require_resource_accessible(
        self,
        db: AsyncSession,
        *,
        resource_id: int,
        user: User,
    ) -> LibraryResource:
        """Verify a resource can be used (e.g. placed on tabletop) by this user.
        Currently only the owner can use their own resources. Extend here when
        sharing rules evolve."""
        resource = await self._get_or_404(db, resource_id=resource_id)
        await self._require_owner(resource, user)
        return resource
