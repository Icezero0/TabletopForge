from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.assets.models import Asset


class AssetRepository:
    async def create_asset(
        self,
        db: AsyncSession,
        *,
        asset_type: str,
        owner_id: int | None,
        feedback_id: int | None,
        original_filename: str | None,
        storage_path: str,
        content_type: str,
        size_bytes: int,
    ) -> Asset:
        asset = Asset(
            asset_type=asset_type,
            owner_id=owner_id,
            feedback_id=feedback_id,
            original_filename=original_filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
        )
        db.add(asset)
        await db.flush()
        await db.refresh(asset)
        return asset

    async def get_asset_by_id(self, db: AsyncSession, asset_id: int) -> Asset | None:
        result = await db.execute(select(Asset).where(Asset.id == asset_id))
        return result.scalar_one_or_none()
