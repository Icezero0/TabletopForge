from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.library.models import LibraryResource


class LibraryRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        type: str,
        name: str,
        primary_asset_id: int | None = None,
        meta: dict | None = None,
    ) -> LibraryResource:
        resource = LibraryResource(
            owner_id=owner_id,
            type=type,
            name=name,
            primary_asset_id=primary_asset_id,
            meta=meta or {},
        )
        db.add(resource)
        await db.flush()
        await db.refresh(resource)
        return resource

    async def get_by_id(
        self,
        db: AsyncSession,
        *,
        resource_id: int,
    ) -> LibraryResource | None:
        result = await db.execute(
            select(LibraryResource).where(LibraryResource.id == resource_id)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        type: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[LibraryResource], int]:
        query = select(LibraryResource).where(LibraryResource.owner_id == owner_id)
        if type is not None:
            query = query.where(LibraryResource.type == type)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        result = await db.execute(
            query.order_by(LibraryResource.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def update_name(
        self,
        db: AsyncSession,
        *,
        resource: LibraryResource,
        name: str,
    ) -> LibraryResource:
        resource.name = name
        await db.flush()
        await db.refresh(resource)
        return resource

    async def update(
        self,
        db: AsyncSession,
        *,
        resource: LibraryResource,
        name: str,
        meta_patch: dict | None = None,
    ) -> LibraryResource:
        resource.name = name
        if meta_patch is not None:
            resource.meta = {**resource.meta, **meta_patch}
        await db.flush()
        await db.refresh(resource)
        return resource

    async def update_grid(
        self,
        db: AsyncSession,
        *,
        resource: LibraryResource,
        map_grid_x: float | None,
        map_grid_y: float | None,
        map_grid_size: float | None,
        map_grid_cell_height: float | None = None,
        map_grid_calibration: list | None = None,
    ) -> LibraryResource:
        resource.map_grid_x = map_grid_x
        resource.map_grid_y = map_grid_y
        resource.map_grid_size = map_grid_size
        resource.map_grid_cell_height = map_grid_cell_height
        resource.map_grid_calibration = map_grid_calibration
        await db.flush()
        await db.refresh(resource)
        return resource

    async def delete(self, db: AsyncSession, *, resource: LibraryResource) -> None:
        await db.delete(resource)
        await db.flush()

    async def adjust_usage_count(
        self,
        db: AsyncSession,
        *,
        resource: LibraryResource,
        delta: int,
    ) -> LibraryResource:
        """delta=+1 递增（放上桌面），delta=-1 递减（从桌面移除）。不会低于 0。"""
        resource.usage_count = max(0, resource.usage_count + delta)
        await db.flush()
        await db.refresh(resource)
        return resource
