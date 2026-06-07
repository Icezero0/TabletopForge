from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.modules.assets.constants import AssetType
from app.modules.assets.service import AssetService
from app.modules.character.models import Character, CharacterState
from app.modules.character.presenter import (
    build_character_state_broadcast,
    present_token_state_summary,
)
from app.modules.character.repository import CharacterRepository
from app.modules.character.state_repository import CharacterStateRepository
from app.modules.rooms.characters.repository import RoomCharacterRepository
from app.modules.rooms.constants import GamePermission, GameRole
from app.modules.rooms.game_permissions import require_game_permission
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.models import RoomDrawing, RoomMap, RoomTabletopSettings, RoomToken
from app.modules.rooms.room.service import RoomService
from app.modules.rooms.tabletop.repository import RoomTabletopRepository
from app.modules.rooms.tabletop.constants import TokenType
from app.modules.rooms.tabletop.schemas import (
    RoomDrawingCreate,
    RoomDrawingPatch,
    RoomDrawingResponse,
    RoomMapPatch,
    RoomMapResponse,
    RoomTabletopSettingsPatch,
    RoomTabletopSettingsResponse,
    RoomTabletopSnapshotResponse,
    RoomTokenPatch,
    RoomTokenResponse,
    SpawnCharacterTokenRequest,
    TokenStateSummary,
)
from app.modules.users.models import User


class RoomTabletopService:
    def __init__(self) -> None:
        self.repo = RoomTabletopRepository()
        self.membership_service = RoomMembershipService()
        self.room_service = RoomService()
        self.asset_service = AssetService()
        self.room_character_repo = RoomCharacterRepository()
        self.character_repo = CharacterRepository()
        self.state_repo = CharacterStateRepository()

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

    async def _require_token_write_access(
        self,
        db: AsyncSession,
        game_role: GameRole,
        *,
        user: User,
        token: RoomToken | None = None,
        for_create: bool = False,
    ) -> None:
        if game_role == GameRole.GM:
            require_game_permission(game_role, GamePermission.MANAGE_ANY_TOKEN)
            return
        if game_role == GameRole.PL:
            require_game_permission(game_role, GamePermission.MOVE_OWN_CHARACTER_TOKEN)
            if for_create:
                return
            if token is None:
                return
            if token.linked_character_id is not None:
                character = await self.character_repo.get_by_id(
                    db,
                    character_id=token.linked_character_id,
                )
                if character is None or character.owner_id != user.id:
                    raise ForbiddenError(
                        "You do not have permission to perform this action",
                        reason=ErrorReason.ROOM_PERMISSION_DENIED,
                        details={"token_id": token.id},
                    )
                return
            if token.owner_user_id != user.id:
                raise ForbiddenError(
                    "You do not have permission to perform this action",
                    reason=ErrorReason.ROOM_PERMISSION_DENIED,
                    details={"token_id": token.id},
                )
            return
        raise ForbiddenError(
            "You do not have permission to perform this action",
            reason=ErrorReason.ROOM_PERMISSION_DENIED,
            details={"game_role": game_role},
        )

    async def _validate_linked_character_in_room(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        character_id: int,
    ) -> Character:
        in_room = await self.room_character_repo.is_character_in_room(
            db,
            character_id=character_id,
            room_id=room_id,
        )
        if not in_room:
            raise BadRequestError(
                "Character is not in this room library",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                details={"character_id": character_id, "room_id": room_id},
            )
        character = await self.character_repo.get_by_id(db, character_id=character_id)
        if character is None:
            raise BadRequestError(
                "Character not found",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                details={"character_id": character_id},
            )
        return character

    def _build_state_summary(
        self,
        *,
        character: Character,
        state: CharacterState | None,
        game_role: GameRole,
        viewer_user_id: int,
    ) -> TokenStateSummary:
        return present_token_state_summary(
            character,
            state,
            game_role=game_role,
            viewer_user_id=viewer_user_id,
        )

    async def _token_responses(
        self,
        db: AsyncSession,
        tokens: list[RoomToken],
        *,
        game_role: GameRole,
        viewer_user_id: int,
    ) -> list[RoomTokenResponse]:
        if not tokens:
            return []
        character_ids = [
            t.linked_character_id for t in tokens if t.linked_character_id is not None
        ]
        characters = await self.character_repo.get_by_ids(db, character_ids=character_ids)
        states = await self.state_repo.get_by_character_ids(db, character_ids=character_ids)
        room_id = tokens[0].room_id
        responses: list[RoomTokenResponse] = []
        for token in tokens:
            base = RoomTokenResponse.model_validate(token)
            if token.linked_character_id is None:
                responses.append(base.model_copy(update={"state_summary": None}))
                continue
            character = characters.get(token.linked_character_id)
            if character is None:
                responses.append(base.model_copy(update={"state_summary": None}))
                continue
            summary = self._build_state_summary(
                character=character,
                state=states.get(token.linked_character_id),
                game_role=game_role,
                viewer_user_id=viewer_user_id,
            )
            responses.append(
                base.model_copy(
                    update={
                        "state_summary": summary,
                        "linked_character_owner_id": character.owner_id,
                    }
                )
            )
        return responses

    async def _token_response(
        self,
        db: AsyncSession,
        token: RoomToken,
        *,
        game_role: GameRole,
        viewer_user_id: int,
    ) -> RoomTokenResponse:
        responses = await self._token_responses(
            db,
            [token],
            game_role=game_role,
            viewer_user_id=viewer_user_id,
        )
        return responses[0]

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
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        settings = await self._get_or_create_settings(db, room_id=room_id)
        await db.commit()
        maps = await self.repo.list_maps(db, room_id=room_id)
        drawings = await self.repo.list_drawings(db, room_id=room_id)
        tokens = await self.repo.list_tokens(db, room_id=room_id)
        return RoomTabletopSnapshotResponse(
            settings=RoomTabletopSettingsResponse.model_validate(settings),
            maps=[RoomMapResponse.model_validate(m) for m in maps],
            drawings=[RoomDrawingResponse.model_validate(d) for d in drawings],
            tokens=await self._token_responses(
                db,
                tokens,
                game_role=game_role,
                viewer_user_id=user.id,
            ),
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

    async def create_token(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        name: str,
        x: float,
        y: float,
        file: UploadFile | None = None,
        linked_character_id: int | None = None,
    ) -> RoomTokenResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        await self._require_token_write_access(
            db, game_role, user=user, for_create=True
        )

        name = name.strip()
        if not name:
            raise BadRequestError(
                "Token name is required",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
            )

        if linked_character_id is not None:
            await self._validate_linked_character_in_room(
                db,
                room_id=room_id,
                character_id=linked_character_id,
            )

        settings = await self._get_or_create_settings(db, room_id=room_id)
        existing_tokens = await self.repo.list_tokens(db, room_id=room_id)
        next_z_index = max((t.z_index for t in existing_tokens), default=-1) + 1

        asset_id: int | None = None
        if file is not None and file.filename:
            asset = await self.asset_service.create_image_asset(
                db,
                file=file,
                asset_type=AssetType.TOKEN_IMAGE,
                owner_id=user.id,
            )
            asset_id = asset.id

        token = await self.repo.create_token(
            db,
            room_id=room_id,
            name=name,
            x=x,
            y=y,
            width=settings.grid_cell_ft,
            height=settings.grid_cell_ft,
            owner_user_id=user.id,
            asset_id=asset_id,
            linked_character_id=linked_character_id,
            token_type=TokenType.CHARACTER.value,
            z_index=next_z_index,
        )
        await db.commit()
        return await self._token_response(
            db,
            token,
            game_role=game_role,
            viewer_user_id=user.id,
        )

    async def spawn_character_token(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        character_id: int,
        user: User,
        payload: SpawnCharacterTokenRequest,
    ) -> RoomTokenResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        character = await self._validate_linked_character_in_room(
            db,
            room_id=room_id,
            character_id=character_id,
        )

        if game_role == GameRole.GM:
            require_game_permission(game_role, GamePermission.MANAGE_ANY_TOKEN)
        elif game_role == GameRole.PL:
            if character.owner_id != user.id:
                raise ForbiddenError(
                    "You do not have permission to perform this action",
                    reason=ErrorReason.ROOM_PERMISSION_DENIED,
                    details={"character_id": character_id},
                )
        else:
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"game_role": game_role},
            )

        settings = await self._get_or_create_settings(db, room_id=room_id)
        existing_tokens = await self.repo.list_tokens(db, room_id=room_id)
        next_z_index = max((t.z_index for t in existing_tokens), default=-1) + 1

        token_name = (payload.name or character.name).strip()
        if not token_name:
            raise BadRequestError(
                "Token name is required",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
            )

        primary_config = next(
            (cfg for cfg in (character.token_configs or []) if cfg.is_primary),
            None,
        )
        spawn_asset_id = (
            primary_config.asset_id
            if primary_config and primary_config.asset_id is not None
            else character.token_image_asset_id or character.portrait_asset_id
        )

        token = await self.repo.create_token(
            db,
            room_id=room_id,
            name=token_name,
            x=payload.x if payload.x is not None else 0.0,
            y=payload.y if payload.y is not None else 0.0,
            width=settings.grid_cell_ft,
            height=settings.grid_cell_ft,
            owner_user_id=user.id,
            asset_id=spawn_asset_id,
            linked_character_id=character_id,
            token_type=TokenType.CHARACTER.value,
            z_index=next_z_index,
        )
        await db.commit()
        return await self._token_response(
            db,
            token,
            game_role=game_role,
            viewer_user_id=user.id,
        )

    async def patch_token(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        token_id: int,
        user: User,
        payload: RoomTokenPatch,
    ) -> RoomTokenResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        token = await self.repo.get_token(db, token_id=token_id, room_id=room_id)
        if token is None:
            raise NotFoundError(
                "Token not found",
                reason=ErrorReason.ROOM_NOT_FOUND,
                details={"token_id": token_id},
            )

        await self._require_token_write_access(
            db, game_role, user=user, token=token
        )

        position_or_size_changed = any(
            value is not None
            for value in (payload.x, payload.y, payload.width, payload.height, payload.rotation)
        )
        if position_or_size_changed and token.locked:
            raise BadRequestError(
                "Token is locked",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                details={"token_id": token_id},
            )

        linked_character_id_set = "linked_character_id" in payload.model_fields_set
        if linked_character_id_set and payload.linked_character_id is not None:
            await self._validate_linked_character_in_room(
                db,
                room_id=room_id,
                character_id=payload.linked_character_id,
            )

        updated = await self.repo.update_token(
            db,
            token=token,
            name=payload.name.strip() if payload.name is not None else None,
            x=payload.x,
            y=payload.y,
            width=payload.width,
            height=payload.height,
            rotation=payload.rotation,
            z_index=payload.z_index,
            visible=payload.visible,
            locked=payload.locked,
            linked_character_id=payload.linked_character_id,
            _linked_character_id_set=linked_character_id_set,
        )
        await db.commit()
        return await self._token_response(
            db,
            updated,
            game_role=game_role,
            viewer_user_id=user.id,
        )

    async def delete_token(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        token_id: int,
        user: User,
    ) -> None:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        token = await self.repo.get_token(db, token_id=token_id, room_id=room_id)
        if token is None:
            raise NotFoundError(
                "Token not found",
                reason=ErrorReason.ROOM_NOT_FOUND,
                details={"token_id": token_id},
            )

        await self._require_token_write_access(
            db, game_role, user=user, token=token
        )
        await self.repo.delete_token(db, token=token)
        await db.commit()

    async def user_can_read_token_asset(
        self,
        db: AsyncSession,
        *,
        asset_id: int,
        user_id: int,
    ) -> bool:
        return await self.repo.user_can_read_token_asset(
            db,
            asset_id=asset_id,
            user_id=user_id,
        )

    async def build_character_state_broadcast(
        self,
        db: AsyncSession,
        *,
        character_id: int,
    ) -> dict | None:
        character = await self.character_repo.get_by_id(db, character_id=character_id)
        if character is None:
            return None
        state = await self.state_repo.get_by_character_id(
            db,
            character_id=character_id,
        )
        if state is None:
            return None
        return build_character_state_broadcast(character, state)

    async def build_token_state_summary_for_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
    ) -> TokenStateSummary | None:
        character = await self.character_repo.get_by_id(db, character_id=character_id)
        if character is None:
            return None
        state = await self.state_repo.get_by_character_id(
            db,
            character_id=character_id,
        )
        return self._build_state_summary(
            character=character,
            state=state,
            game_role=GameRole.GM,
            viewer_user_id=character.owner_id,
        )
