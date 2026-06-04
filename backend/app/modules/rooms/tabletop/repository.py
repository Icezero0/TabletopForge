from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rooms.models import RoomDrawing, RoomMap, RoomMember, RoomTabletopSettings
from app.modules.rooms.tabletop.constants import DEFAULT_GRID_CELL_FT, DEFAULT_GRID_CELL_PX


class RoomTabletopRepository:
    async def get_settings(
        self,
        db: AsyncSession,
        *,
        room_id: int,
    ) -> RoomTabletopSettings | None:
        result = await db.execute(
            select(RoomTabletopSettings).where(RoomTabletopSettings.room_id == room_id)
        )
        return result.scalar_one_or_none()

    async def create_default_settings(
        self,
        db: AsyncSession,
        *,
        room_id: int,
    ) -> RoomTabletopSettings:
        settings = RoomTabletopSettings(
            room_id=room_id,
            grid_cell_ft=DEFAULT_GRID_CELL_FT,
            grid_cell_px=DEFAULT_GRID_CELL_PX,
        )
        db.add(settings)
        await db.flush()
        await db.refresh(settings)
        return settings

    async def update_settings(
        self,
        db: AsyncSession,
        *,
        settings: RoomTabletopSettings,
        grid_cell_ft: float | None,
        grid_cell_px: int | None,
    ) -> RoomTabletopSettings:
        if grid_cell_ft is not None:
            settings.grid_cell_ft = grid_cell_ft
        if grid_cell_px is not None:
            settings.grid_cell_px = grid_cell_px
        await db.flush()
        await db.refresh(settings)
        return settings

    async def list_maps(self, db: AsyncSession, *, room_id: int) -> list[RoomMap]:
        result = await db.execute(
            select(RoomMap).where(RoomMap.room_id == room_id).order_by(RoomMap.z_index, RoomMap.id)
        )
        return list(result.scalars().all())

    async def count_maps(self, db: AsyncSession, *, room_id: int) -> int:
        result = await db.execute(select(RoomMap).where(RoomMap.room_id == room_id))
        return len(result.scalars().all())

    async def get_map(self, db: AsyncSession, *, map_id: int, room_id: int) -> RoomMap | None:
        result = await db.execute(
            select(RoomMap).where(RoomMap.id == map_id, RoomMap.room_id == room_id)
        )
        return result.scalar_one_or_none()

    async def create_map(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        asset_id: int,
        x: float = 0.0,
        y: float = 0.0,
        scale: float = 1.0,
        locked: bool = False,
        z_index: int = 0,
    ) -> RoomMap:
        room_map = RoomMap(
            room_id=room_id,
            asset_id=asset_id,
            x=x,
            y=y,
            scale=scale,
            locked=locked,
            z_index=z_index,
        )
        db.add(room_map)
        await db.flush()
        await db.refresh(room_map)
        return room_map

    async def update_map(
        self,
        db: AsyncSession,
        *,
        room_map: RoomMap,
        x: float | None = None,
        y: float | None = None,
        scale: float | None = None,
        locked: bool | None = None,
        z_index: int | None = None,
    ) -> RoomMap:
        if x is not None:
            room_map.x = x
        if y is not None:
            room_map.y = y
        if scale is not None:
            room_map.scale = scale
        if locked is not None:
            room_map.locked = locked
        if z_index is not None:
            room_map.z_index = z_index
        await db.flush()
        await db.refresh(room_map)
        return room_map

    async def delete_map(self, db: AsyncSession, *, room_map: RoomMap) -> None:
        await db.delete(room_map)
        await db.flush()

    async def list_drawings(self, db: AsyncSession, *, room_id: int) -> list[RoomDrawing]:
        result = await db.execute(
            select(RoomDrawing)
            .where(RoomDrawing.room_id == room_id)
            .order_by(RoomDrawing.z_index, RoomDrawing.id)
        )
        return list(result.scalars().all())

    async def get_drawing(
        self,
        db: AsyncSession,
        *,
        drawing_id: int,
        room_id: int,
    ) -> RoomDrawing | None:
        result = await db.execute(
            select(RoomDrawing).where(
                RoomDrawing.id == drawing_id,
                RoomDrawing.room_id == room_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_drawing(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        kind: str,
        geometry: dict,
        style: dict,
        z_index: int,
        created_by_user_id: int,
    ) -> RoomDrawing:
        drawing = RoomDrawing(
            room_id=room_id,
            kind=kind,
            geometry=geometry,
            style=style,
            z_index=z_index,
            created_by_user_id=created_by_user_id,
        )
        db.add(drawing)
        await db.flush()
        await db.refresh(drawing)
        return drawing

    async def update_drawing(
        self,
        db: AsyncSession,
        *,
        drawing: RoomDrawing,
        geometry: dict | None = None,
        style: dict | None = None,
        z_index: int | None = None,
    ) -> RoomDrawing:
        if geometry is not None:
            drawing.geometry = geometry
        if style is not None:
            drawing.style = style
        if z_index is not None:
            drawing.z_index = z_index
        await db.flush()
        await db.refresh(drawing)
        return drawing

    async def delete_drawings_by_ids(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        drawing_ids: list[int],
    ) -> list[int]:
        if not drawing_ids:
            return []
        result = await db.execute(
            select(RoomDrawing.id).where(
                RoomDrawing.room_id == room_id,
                RoomDrawing.id.in_(drawing_ids),
            )
        )
        existing_ids = [row[0] for row in result.all()]
        if not existing_ids:
            return []
        await db.execute(
            delete(RoomDrawing).where(
                RoomDrawing.room_id == room_id,
                RoomDrawing.id.in_(existing_ids),
            )
        )
        await db.flush()
        return existing_ids

    async def user_can_read_map_asset(
        self,
        db: AsyncSession,
        *,
        asset_id: int,
        user_id: int,
    ) -> bool:
        result = await db.execute(
            select(RoomMember.room_id)
            .join(RoomMap, RoomMap.room_id == RoomMember.room_id)
            .where(RoomMap.asset_id == asset_id, RoomMember.user_id == user_id)
        )
        return result.first() is not None
