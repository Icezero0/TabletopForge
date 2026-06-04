from sqlalchemy import func, select
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
        content_hash: str,
        ref_count: int = 1,
    ) -> Asset:
        asset = Asset(
            asset_type=asset_type,
            owner_id=owner_id,
            feedback_id=feedback_id,
            original_filename=original_filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
            content_hash=content_hash,
            ref_count=ref_count,
        )
        db.add(asset)
        await db.flush()
        await db.refresh(asset)
        return asset

    async def get_asset_by_id(self, db: AsyncSession, asset_id: int) -> Asset | None:
        result = await db.execute(select(Asset).where(Asset.id == asset_id))
        return result.scalar_one_or_none()

    async def find_asset_by_fingerprint(
        self,
        db: AsyncSession,
        *,
        asset_type: str,
        content_hash: str,
        content_type: str,
        size_bytes: int,
    ) -> Asset | None:
        result = await db.execute(
            select(Asset).where(
                Asset.asset_type == asset_type,
                Asset.content_hash == content_hash,
                Asset.content_type == content_type,
                Asset.size_bytes == size_bytes,
            )
        )
        return result.scalar_one_or_none()

    async def get_assets(
        self,
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
        asset_type: str | None = None,
    ) -> tuple[list[Asset], int]:
        conditions = [Asset.asset_type.in_(["image", "audio"])]
        if asset_type is not None:
            conditions.append(Asset.asset_type == asset_type)

        total_result = await db.execute(
            select(func.count()).select_from(Asset).where(*conditions)
        )
        total = int(total_result.scalar_one())

        result = await db.execute(
            select(Asset)
            .where(*conditions)
            .order_by(Asset.created_at.desc(), Asset.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars()), total

    async def delete_asset(self, db: AsyncSession, asset: Asset) -> None:
        await db.delete(asset)

    async def save_asset(self, db: AsyncSession, asset: Asset) -> Asset:
        db.add(asset)
        await db.flush()
        await db.refresh(asset)
        return asset
