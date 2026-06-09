from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.library.models import LibraryResource
from app.modules.rooms.models import RoomDrawing, RoomMap, RoomMember, RoomTabletopSettings, RoomToken
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
        combat_state: dict | None = None,
        combat_state_provided: bool = False,
    ) -> RoomTabletopSettings:
        if grid_cell_ft is not None:
            settings.grid_cell_ft = grid_cell_ft
        if grid_cell_px is not None:
            settings.grid_cell_px = grid_cell_px
        if combat_state_provided:
            settings.combat_state = combat_state
        await db.flush()
        await db.refresh(settings)
        return settings

    async def list_maps(self, db: AsyncSession, *, room_id: int) -> list[RoomMap]:
        result = await db.execute(
            select(RoomMap)
            .where(RoomMap.room_id == room_id)
            .options(selectinload(RoomMap.library_resource))
            .order_by(RoomMap.z_index, RoomMap.id)
        )
        return list(result.scalars().all())

    async def count_maps(self, db: AsyncSession, *, room_id: int) -> int:
        result = await db.execute(select(RoomMap).where(RoomMap.room_id == room_id))
        return len(result.scalars().all())

    async def get_map(self, db: AsyncSession, *, map_id: int, room_id: int) -> RoomMap | None:
        result = await db.execute(
            select(RoomMap)
            .where(RoomMap.id == map_id, RoomMap.room_id == room_id)
            .options(selectinload(RoomMap.library_resource))
        )
        return result.scalar_one_or_none()

    async def create_map(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        library_resource_id: int,
        x: float = 0.0,
        y: float = 0.0,
        scale: float = 1.0,
        locked: bool = False,
        z_index: int = 0,
    ) -> RoomMap:
        room_map = RoomMap(
            room_id=room_id,
            library_resource_id=library_resource_id,
            x=x,
            y=y,
            scale=scale,
            locked=locked,
            z_index=z_index,
        )
        db.add(room_map)
        await db.flush()
        result = await db.execute(
            select(RoomMap)
            .where(RoomMap.id == room_map.id)
            .options(selectinload(RoomMap.library_resource))
        )
        return result.scalar_one()

    async def update_map(
        self,
        db: AsyncSession,
        *,
        room_map: RoomMap,
        x: float | None = None,
        y: float | None = None,
        scale: float | None = None,
        scale_x: float | None = None,
        scale_y: float | None = None,
        _scale_x_set: bool = False,
        _scale_y_set: bool = False,
        locked: bool | None = None,
        z_index: int | None = None,
    ) -> RoomMap:
        if x is not None:
            room_map.x = x
        if y is not None:
            room_map.y = y
        if scale is not None:
            room_map.scale = scale
        if _scale_x_set:
            room_map.scale_x = scale_x
        if _scale_y_set:
            room_map.scale_y = scale_y
        if locked is not None:
            room_map.locked = locked
        if z_index is not None:
            room_map.z_index = z_index
        await db.flush()
        result = await db.execute(
            select(RoomMap)
            .where(RoomMap.id == room_map.id)
            .options(selectinload(RoomMap.library_resource))
        )
        return result.scalar_one()

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
            .join(LibraryResource, LibraryResource.id == RoomMap.library_resource_id)
            .where(LibraryResource.primary_asset_id == asset_id, RoomMember.user_id == user_id)
        )
        return result.first() is not None

    async def list_tokens(self, db: AsyncSession, *, room_id: int) -> list[RoomToken]:
        result = await db.execute(
            select(RoomToken)
            .where(RoomToken.room_id == room_id)
            .options(selectinload(RoomToken.library_resource))
            .order_by(RoomToken.z_index, RoomToken.id)
        )
        return list(result.scalars().all())

    async def get_token(
        self,
        db: AsyncSession,
        *,
        token_id: int,
        room_id: int,
    ) -> RoomToken | None:
        result = await db.execute(
            select(RoomToken)
            .where(RoomToken.id == token_id, RoomToken.room_id == room_id)
            .options(selectinload(RoomToken.library_resource))
        )
        return result.scalar_one_or_none()

    async def create_token(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        name: str,
        x: float,
        y: float,
        width: float,
        height: float,
        owner_user_id: int,
        linked_character_id: int,
        library_resource_id: int | None = None,
        rotation: float = 0.0,
        z_index: int = 0,
        visible: bool = True,
        locked: bool = False,
        panel: dict | None = None,
    ) -> RoomToken:
        token = RoomToken(
            room_id=room_id,
            library_resource_id=library_resource_id,
            linked_character_id=linked_character_id,
            name=name,
            x=x,
            y=y,
            width=width,
            height=height,
            rotation=rotation,
            z_index=z_index,
            visible=visible,
            locked=locked,
            panel=panel,
            owner_user_id=owner_user_id,
        )
        db.add(token)
        await db.flush()
        result = await db.execute(
            select(RoomToken)
            .where(RoomToken.id == token.id)
            .options(selectinload(RoomToken.library_resource))
        )
        return result.scalar_one()

    async def update_token(
        self,
        db: AsyncSession,
        *,
        token: RoomToken,
        name: str | None = None,
        x: float | None = None,
        y: float | None = None,
        width: float | None = None,
        height: float | None = None,
        rotation: float | None = None,
        z_index: int | None = None,
        visible: bool | None = None,
        locked: bool | None = None,
        linked_character_id: int | None = None,
        _linked_character_id_set: bool = False,
        panel_merge: dict | None = None,
    ) -> RoomToken:
        if name is not None:
            token.name = name
        if x is not None:
            token.x = x
        if y is not None:
            token.y = y
        if width is not None:
            token.width = width
        if height is not None:
            token.height = height
        if rotation is not None:
            token.rotation = rotation
        if z_index is not None:
            token.z_index = z_index
        if visible is not None:
            token.visible = visible
        if locked is not None:
            token.locked = locked
        if _linked_character_id_set:
            token.linked_character_id = linked_character_id
        if panel_merge is not None:
            panel = {**(token.panel or {}), **panel_merge}
            panel.pop("damage_taken", None)
            token.panel = panel
        await db.flush()
        result = await db.execute(
            select(RoomToken)
            .where(RoomToken.id == token.id)
            .options(selectinload(RoomToken.library_resource))
        )
        return result.scalar_one()

    async def delete_token(self, db: AsyncSession, *, token: RoomToken) -> None:
        await db.delete(token)
        await db.flush()

    async def delete_all_tokens_by_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
    ) -> None:
        await db.execute(
            delete(RoomToken).where(RoomToken.linked_character_id == character_id)
        )
        await db.flush()

    async def delete_tokens_by_character(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        character_id: int,
    ) -> list[int]:
        result = await db.execute(
            select(RoomToken.id).where(
                RoomToken.room_id == room_id,
                RoomToken.linked_character_id == character_id,
            )
        )
        token_ids = [row[0] for row in result.all()]
        if token_ids:
            await db.execute(
                delete(RoomToken).where(RoomToken.id.in_(token_ids))
            )
            await db.flush()
        return token_ids

    async def user_can_read_token_asset(
        self,
        db: AsyncSession,
        *,
        asset_id: int,
        user_id: int,
    ) -> bool:
        result = await db.execute(
            select(RoomMember.room_id)
            .join(RoomToken, RoomToken.room_id == RoomMember.room_id)
            .join(LibraryResource, LibraryResource.id == RoomToken.library_resource_id)
            .where(LibraryResource.primary_asset_id == asset_id, RoomMember.user_id == user_id)
        )
        return result.first() is not None
