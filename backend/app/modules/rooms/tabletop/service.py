from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.modules.assets.constants import AssetType
from app.modules.assets.service import AssetService
from app.modules.rooms.constants import GamePermission, GameRole
from app.modules.rooms.game_permissions import require_game_permission
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.models import RoomDrawing, RoomMap, RoomTabletopSettings
from app.modules.rooms.room.service import RoomService
from app.modules.rooms.tabletop.repository import RoomTabletopRepository
from app.modules.rooms.tabletop.schemas import (
    RoomDrawingCreate,
    RoomDrawingPatch,
    RoomDrawingResponse,
    RoomMapPatch,
    RoomMapResponse,
    RoomTabletopSettingsPatch,
    RoomTabletopSettingsResponse,
    RoomTabletopSnapshotResponse,
)
from app.modules.users.models import User


class RoomTabletopService:
    def __init__(self) -> None:
        self.repo = RoomTabletopRepository()
        self.membership_service = RoomMembershipService()
        self.room_service = RoomService()
        self.asset_service = AssetService()

    async def _require_member_game_role(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
    ) -> GameRole:
        await self.room_service.get_room_by_id(db, room_id)
        game_role = await self.membership_service.find_game_role(
            db,
            room_id=room_id,
            user_id=user.id,
        )
        if game_role is None:
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"room_id": room_id},
            )
        return game_role

    async def _get_or_create_settings(
        self,
        db: AsyncSession,
        *,
        room_id: int,
    ) -> RoomTabletopSettings:
        settings = await self.repo.get_settings(db, room_id=room_id)
        if settings is not None:
            return settings
        return await self.repo.create_default_settings(db, room_id=room_id)

    async def get_snapshot(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
    ) -> RoomTabletopSnapshotResponse:
        await self._require_member_game_role(db, room_id=room_id, user=user)
        settings = await self._get_or_create_settings(db, room_id=room_id)
        await db.commit()
        maps = await self.repo.list_maps(db, room_id=room_id)
        drawings = await self.repo.list_drawings(db, room_id=room_id)
        return RoomTabletopSnapshotResponse(
            settings=RoomTabletopSettingsResponse.model_validate(settings),
            maps=[RoomMapResponse.model_validate(m) for m in maps],
            drawings=[RoomDrawingResponse.model_validate(d) for d in drawings],
        )

    async def patch_settings(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        payload: RoomTabletopSettingsPatch,
    ) -> RoomTabletopSettingsResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        if game_role != GameRole.GM:
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"game_role": game_role},
            )

        settings = await self._get_or_create_settings(db, room_id=room_id)
        updated = await self.repo.update_settings(
            db,
            settings=settings,
            grid_cell_ft=payload.grid_cell_ft,
            grid_cell_px=payload.grid_cell_px,
        )
        await db.commit()
        return RoomTabletopSettingsResponse.model_validate(updated)

    async def create_map(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        file: UploadFile,
        x: float = 0.0,
        y: float = 0.0,
        scale: float = 1.0,
    ) -> RoomMapResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        require_game_permission(game_role, GamePermission.UPLOAD_MAP)

        existing_maps = await self.repo.list_maps(db, room_id=room_id)
        next_z_index = (
            max((m.z_index for m in existing_maps), default=-1) + 1
            if existing_maps
            else 0
        )

        asset = await self.asset_service.create_image_asset(
            db,
            file=file,
            asset_type=AssetType.MAP_BACKGROUND,
            owner_id=user.id,
        )
        room_map = await self.repo.create_map(
            db,
            room_id=room_id,
            asset_id=asset.id,
            x=x,
            y=y,
            scale=scale,
            z_index=next_z_index,
        )
        await db.commit()
        return RoomMapResponse.model_validate(room_map)

    async def patch_map(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        map_id: int,
        user: User,
        payload: RoomMapPatch,
    ) -> RoomMapResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        room_map = await self.repo.get_map(db, map_id=map_id, room_id=room_id)
        if room_map is None:
            raise NotFoundError(
                "Map not found",
                reason=ErrorReason.ROOM_NOT_FOUND,
                details={"map_id": map_id},
            )

        if payload.locked is not None:
            require_game_permission(game_role, GamePermission.LOCK_MAP)

        position_or_scale_changed = any(
            value is not None for value in (payload.x, payload.y, payload.scale, payload.z_index)
        )
        if position_or_scale_changed:
            if room_map.locked:
                raise BadRequestError(
                    "Map is locked",
                    reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                    details={"map_id": map_id},
                )
            require_game_permission(game_role, GamePermission.MOVE_UNLOCKED_MAP)

        updated = await self.repo.update_map(
            db,
            room_map=room_map,
            x=payload.x,
            y=payload.y,
            scale=payload.scale,
            locked=payload.locked,
            z_index=payload.z_index,
        )
        await db.commit()
        return RoomMapResponse.model_validate(updated)

    async def delete_map(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        map_id: int,
        user: User,
    ) -> None:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        require_game_permission(game_role, GamePermission.DELETE_MAP)

        room_map = await self.repo.get_map(db, map_id=map_id, room_id=room_id)
        if room_map is None:
            raise NotFoundError(
                "Map not found",
                reason=ErrorReason.ROOM_NOT_FOUND,
                details={"map_id": map_id},
            )
        await self.repo.delete_map(db, room_map=room_map)
        await db.commit()

    async def create_drawing(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        payload: RoomDrawingCreate,
    ) -> RoomDrawingResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        require_game_permission(game_role, GamePermission.MANAGE_DRAWINGS)

        drawing = await self.repo.create_drawing(
            db,
            room_id=room_id,
            kind=payload.kind.value,
            geometry=payload.geometry,
            style=payload.style,
            z_index=payload.z_index,
            created_by_user_id=user.id,
        )
        await db.commit()
        return RoomDrawingResponse.model_validate(drawing)

    async def patch_drawing(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        drawing_id: int,
        user: User,
        payload: RoomDrawingPatch,
    ) -> RoomDrawingResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        require_game_permission(game_role, GamePermission.MANAGE_DRAWINGS)

        drawing = await self.repo.get_drawing(db, drawing_id=drawing_id, room_id=room_id)
        if drawing is None:
            raise NotFoundError(
                "Drawing not found",
                reason=ErrorReason.ROOM_NOT_FOUND,
                details={"drawing_id": drawing_id},
            )

        updated = await self.repo.update_drawing(
            db,
            drawing=drawing,
            geometry=payload.geometry,
            style=payload.style,
            z_index=payload.z_index,
        )
        await db.commit()
        return RoomDrawingResponse.model_validate(updated)

    async def delete_drawings(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        drawing_ids: list[int],
    ) -> list[int]:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        require_game_permission(game_role, GamePermission.ERASE_DRAWINGS)
        deleted_ids = await self.repo.delete_drawings_by_ids(
            db,
            room_id=room_id,
            drawing_ids=drawing_ids,
        )
        await db.commit()
        return deleted_ids

    async def user_can_read_map_asset(
        self,
        db: AsyncSession,
        *,
        asset_id: int,
        user_id: int,
    ) -> bool:
        return await self.repo.user_can_read_map_asset(
            db,
            asset_id=asset_id,
            user_id=user_id,
        )
