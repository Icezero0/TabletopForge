from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.modules.rooms.constants import GameRole
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.models import (
    RoomCharacter,
    RoomDrawing,
    RoomMap,
    RoomScene,
    RoomTabletopSettings,
    RoomToken,
)
from app.modules.rooms.scenes.schemas import RoomSceneCreate, RoomSceneDetailResponse, RoomSceneRename, RoomSceneResponse
from app.modules.rooms.tabletop.constants import DEFAULT_GRID_CELL_FT, DEFAULT_GRID_CELL_PX
from app.modules.rooms.tabletop.repository import RoomTabletopRepository
from app.modules.users.models import User


class RoomSceneService:
    def __init__(self) -> None:
        self.membership_service = RoomMembershipService()
        self.tabletop_repo = RoomTabletopRepository()

    async def _require_member(self, db: AsyncSession, *, room_id: int, user: User) -> GameRole:
        game_role = await self.membership_service.find_game_role(db, room_id=room_id, user_id=user.id)
        if game_role is None:
            raise ForbiddenError(
                "You do not have permission to access this room",
                details={"room_id": room_id},
            )
        return game_role

    async def _require_gm(self, db: AsyncSession, *, room_id: int, user: User) -> None:
        game_role = await self._require_member(db, room_id=room_id, user=user)
        if game_role != GameRole.GM:
            raise ForbiddenError(
                "Only the GM can manage scenes",
                details={"room_id": room_id},
            )

    async def _get_scene(self, db: AsyncSession, *, room_id: int, scene_id: int) -> RoomScene:
        result = await db.execute(
            select(RoomScene).where(RoomScene.id == scene_id, RoomScene.room_id == room_id)
        )
        scene = result.scalar_one_or_none()
        if scene is None:
            raise NotFoundError("Scene not found", details={"scene_id": scene_id})
        return scene

    async def _get_or_create_settings(self, db: AsyncSession, *, room_id: int) -> RoomTabletopSettings:
        settings = await self.tabletop_repo.get_settings(db, room_id=room_id)
        if settings is not None:
            return settings
        return await self.tabletop_repo.create_default_settings(db, room_id=room_id)

    def _empty_snapshot(self) -> dict[str, Any]:
        return {
            "settings": {
                "grid_cell_ft": DEFAULT_GRID_CELL_FT,
                "grid_cell_px": DEFAULT_GRID_CELL_PX,
                "combat_state": None,
                "music_state": None,
                "fog_state": None,
            },
            "maps": [],
            "drawings": [],
            "tokens": [],
            "characters": [],
        }

    async def list_scenes(self, db: AsyncSession, *, room_id: int, user: User) -> list[RoomSceneResponse]:
        await self._require_member(db, room_id=room_id, user=user)
        result = await db.execute(
            select(RoomScene).where(RoomScene.room_id == room_id).order_by(RoomScene.created_at, RoomScene.id)
        )
        scenes = result.scalars().all()
        if not scenes:
            default_scene = RoomScene(
                room_id=room_id,
                name="默认场景",
                snapshot=await self.build_snapshot(db, room_id=room_id),
                is_active=True,
                created_by_user_id=None,
            )
            db.add(default_scene)
            await db.commit()
            await db.refresh(default_scene)
            scenes = [default_scene]
        return [RoomSceneResponse.model_validate(scene) for scene in scenes]

    async def create_scene(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        payload: RoomSceneCreate,
    ) -> RoomSceneResponse:
        await self._require_gm(db, room_id=room_id, user=user)
        has_scene = await db.scalar(select(RoomScene.id).where(RoomScene.room_id == room_id).limit(1))
        scene = RoomScene(
            room_id=room_id,
            name=payload.name,
            snapshot=self._empty_snapshot(),
            is_active=has_scene is None,
            created_by_user_id=user.id,
        )
        db.add(scene)
        await db.flush()
        await db.commit()
        await db.refresh(scene)
        return RoomSceneResponse.model_validate(scene)

    async def rename_scene(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        scene_id: int,
        user: User,
        payload: RoomSceneRename,
    ) -> RoomSceneResponse:
        await self._require_gm(db, room_id=room_id, user=user)
        scene = await self._get_scene(db, room_id=room_id, scene_id=scene_id)
        scene.name = payload.name
        await db.flush()
        await db.commit()
        await db.refresh(scene)
        return RoomSceneResponse.model_validate(scene)

    async def update_scene_snapshot(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        scene_id: int,
        user: User,
    ) -> RoomSceneResponse:
        await self._require_gm(db, room_id=room_id, user=user)
        scene = await self._get_scene(db, room_id=room_id, scene_id=scene_id)
        scene.snapshot = await self.build_snapshot(db, room_id=room_id)
        await db.flush()
        await db.commit()
        await db.refresh(scene)
        return RoomSceneResponse.model_validate(scene)

    async def delete_scene(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        scene_id: int,
        user: User,
    ) -> None:
        await self._require_gm(db, room_id=room_id, user=user)
        scene = await self._get_scene(db, room_id=room_id, scene_id=scene_id)
        remaining_result = await db.execute(
            select(RoomScene).where(RoomScene.room_id == room_id, RoomScene.id != scene_id).order_by(RoomScene.id)
        )
        remaining = remaining_result.scalars().all()
        if not remaining:
            raise BadRequestError("Cannot delete the last scene", details={"scene_id": scene_id})
        if scene.is_active:
            next_scene = remaining[0]
            await self.apply_snapshot(db, room_id=room_id, snapshot=next_scene.snapshot)
            await db.execute(update(RoomScene).where(RoomScene.room_id == room_id).values(is_active=False))
            next_scene.is_active = True
        await db.delete(scene)
        await db.commit()

    async def activate_scene(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        scene_id: int,
        user: User,
    ) -> RoomSceneResponse:
        await self._require_gm(db, room_id=room_id, user=user)
        scene = await self._get_scene(db, room_id=room_id, scene_id=scene_id)
        if scene.is_active:
            return RoomSceneResponse.model_validate(scene)
        active_result = await db.execute(
            select(RoomScene).where(RoomScene.room_id == room_id, RoomScene.is_active.is_(True))
        )
        active_scene = active_result.scalar_one_or_none()
        if active_scene is not None:
            active_scene.snapshot = await self.build_snapshot(db, room_id=room_id)
        await self.apply_snapshot(db, room_id=room_id, snapshot=scene.snapshot)
        await db.execute(update(RoomScene).where(RoomScene.room_id == room_id).values(is_active=False))
        scene.is_active = True
        await db.flush()
        await db.commit()
        await db.refresh(scene)
        return RoomSceneResponse.model_validate(scene)

    async def get_scene_detail(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        scene_id: int,
        user: User,
    ) -> RoomSceneDetailResponse:
        await self._require_member(db, room_id=room_id, user=user)
        scene = await self._get_scene(db, room_id=room_id, scene_id=scene_id)
        return RoomSceneDetailResponse.model_validate(scene)

    async def build_snapshot(self, db: AsyncSession, *, room_id: int) -> dict[str, Any]:
        settings = await self.tabletop_repo.get_settings(db, room_id=room_id)
        maps = await self.tabletop_repo.list_maps(db, room_id=room_id)
        drawings = await self.tabletop_repo.list_drawings(db, room_id=room_id)
        tokens = await self.tabletop_repo.list_tokens(db, room_id=room_id)
        characters_result = await db.execute(
            select(RoomCharacter).where(RoomCharacter.room_id == room_id).order_by(RoomCharacter.created_at, RoomCharacter.id)
        )
        characters = characters_result.scalars().all()
        return {
            "settings": {
                "grid_cell_ft": settings.grid_cell_ft if settings else DEFAULT_GRID_CELL_FT,
                "grid_cell_px": settings.grid_cell_px if settings else DEFAULT_GRID_CELL_PX,
                "combat_state": settings.combat_state if settings else None,
                "music_state": settings.music_state if settings else None,
                "fog_state": settings.fog_state if settings else None,
            },
            "maps": [
                {
                    "id": item.id,
                    "library_resource_id": item.library_resource_id,
                    "x": item.x,
                    "y": item.y,
                    "scale": item.scale,
                    "scale_x": item.scale_x,
                    "scale_y": item.scale_y,
                    "locked": item.locked,
                    "z_index": item.z_index,
                }
                for item in maps
            ],
            "drawings": [
                {
                    "id": item.id,
                    "kind": item.kind,
                    "geometry": item.geometry,
                    "style": item.style,
                    "z_index": item.z_index,
                    "created_by_user_id": item.created_by_user_id,
                }
                for item in drawings
            ],
            "tokens": [
                {
                    "id": item.id,
                    "library_resource_id": item.library_resource_id,
                    "linked_character_id": item.linked_character_id,
                    "name": item.name,
                    "x": item.x,
                    "y": item.y,
                    "width": item.width,
                    "height": item.height,
                    "rotation": item.rotation,
                    "z_index": item.z_index,
                    "visible": item.visible,
                    "locked": item.locked,
                    "panel": item.panel,
                    "owner_user_id": item.owner_user_id,
                }
                for item in tokens
            ],
            "characters": [
                {
                    "id": item.id,
                    "character_id": item.character_id,
                    "is_hidden": item.is_hidden,
                    "hide_data": item.hide_data,
                    "added_by_user_id": item.added_by_user_id,
                }
                for item in characters
            ],
        }

    async def apply_snapshot(self, db: AsyncSession, *, room_id: int, snapshot: dict[str, Any]) -> None:
        await db.execute(delete(RoomDrawing).where(RoomDrawing.room_id == room_id))
        await db.execute(delete(RoomToken).where(RoomToken.room_id == room_id))
        await db.execute(delete(RoomMap).where(RoomMap.room_id == room_id))
        await db.execute(delete(RoomCharacter).where(RoomCharacter.room_id == room_id))

        settings_payload = snapshot.get("settings") or {}
        settings = await self._get_or_create_settings(db, room_id=room_id)
        settings.grid_cell_ft = settings_payload.get("grid_cell_ft") or DEFAULT_GRID_CELL_FT
        settings.grid_cell_px = settings_payload.get("grid_cell_px") or DEFAULT_GRID_CELL_PX
        settings.combat_state = settings_payload.get("combat_state")
        settings.music_state = settings_payload.get("music_state")
        settings.fog_state = settings_payload.get("fog_state")

        for item in snapshot.get("maps") or []:
            db.add(
                RoomMap(
                    id=item.get("id"),
                    room_id=room_id,
                    library_resource_id=item["library_resource_id"],
                    x=item.get("x", 0),
                    y=item.get("y", 0),
                    scale=item.get("scale", 1),
                    scale_x=item.get("scale_x"),
                    scale_y=item.get("scale_y"),
                    locked=item.get("locked", False),
                    z_index=item.get("z_index", 0),
                )
            )
        for item in snapshot.get("drawings") or []:
            db.add(
                RoomDrawing(
                    id=item.get("id"),
                    room_id=room_id,
                    kind=item["kind"],
                    geometry=item.get("geometry") or {},
                    style=item.get("style") or {},
                    z_index=item.get("z_index", 0),
                    created_by_user_id=item["created_by_user_id"],
                )
            )
        for item in snapshot.get("tokens") or []:
            db.add(
                RoomToken(
                    id=item.get("id"),
                    room_id=room_id,
                    library_resource_id=item.get("library_resource_id"),
                    linked_character_id=item["linked_character_id"],
                    name=item["name"],
                    x=item.get("x", 0),
                    y=item.get("y", 0),
                    width=item["width"],
                    height=item.get("height", item["width"]),
                    rotation=item.get("rotation", 0),
                    z_index=item.get("z_index", 0),
                    visible=item.get("visible", True),
                    locked=item.get("locked", False),
                    panel=item.get("panel"),
                    owner_user_id=item["owner_user_id"],
                )
            )
        for item in snapshot.get("characters") or []:
            db.add(
                RoomCharacter(
                    id=item.get("id"),
                    room_id=room_id,
                    character_id=item["character_id"],
                    is_hidden=item.get("is_hidden", False),
                    hide_data=item.get("hide_data", False),
                    added_by_user_id=item["added_by_user_id"],
                )
            )
        await db.flush()
