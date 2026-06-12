import json
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.modules.assets.constants import AssetType
from app.modules.assets.service import AssetService
from app.modules.character.models import CharacterState
from app.modules.character.presenter import present_character_state_summary
from app.modules.character.schemas import CharacterStateCreate, TokenConfigUpsert
from app.modules.character.service import CharacterService
from app.modules.rooms.characters.repository import RoomCharacterRepository
from app.modules.rooms.tabletop.repository import RoomTabletopRepository
from app.modules.rooms.characters.schemas import (
    RoomCharacterDataVisibilityPatch,
    RoomCharacterCreate,
    RoomCharacterEntryResponse,
    RoomCharacterTokenConfigSummary,
    RoomCharacterVisibilityPatch,
)
from app.modules.rooms.constants import GamePermission, GameRole
from app.modules.rooms.game_permissions import require_game_permission
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.models import RoomCharacter
from app.modules.rooms.room.service import RoomService
from app.modules.users.models import User


class RoomCharacterService:
    def __init__(self) -> None:
        self.repo = RoomCharacterRepository()
        self.tabletop_repo = RoomTabletopRepository()
        self.character_service = CharacterService()
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

    async def _require_room_member(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
    ) -> None:
        await self._require_member_game_role(db, room_id=room_id, user=user)

    def _entry_response(
        self,
        entry: RoomCharacter,
        state: CharacterState | None,
        *,
        game_role: GameRole,
        viewer_user_id: int,
    ) -> RoomCharacterEntryResponse:
        character = entry.character
        state_summary = present_character_state_summary(
            character,
            state,
            game_role=game_role,
            viewer_user_id=viewer_user_id,
        )
        token_configs = [
            RoomCharacterTokenConfigSummary(
                id=cfg.id,
                is_primary=cfg.is_primary,
                name=cfg.name,
                asset_id=cfg.asset_id,
            )
            for cfg in (character.token_configs or [])
        ]
        return RoomCharacterEntryResponse(
            room_character_id=entry.id,
            character_id=character.id,
            owner_id=character.owner_id,
            name=character.name,
            player_name=character.player_name,
            token_image_asset_id=character.token_image_asset_id,
            token_configs=token_configs,
            state=state_summary,
            is_hidden=entry.is_hidden,
            hide_data=entry.hide_data,
        )

    async def list_room_characters(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
    ) -> list[RoomCharacterEntryResponse]:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        entries = await self.repo.list_by_room(db, room_id=room_id)
        entries = [e for e in entries if e.character is not None]
        return [
            self._entry_response(
                entry,
                entry.character.state,
                game_role=game_role,
                viewer_user_id=user.id,
            )
            for entry in entries
        ]

    async def remove_room_character(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        room_character_id: int,
        user: User,
    ) -> list[int]:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        entry = await self.repo.get_by_id_and_room(
            db,
            room_character_id=room_character_id,
            room_id=room_id,
        )
        if entry is None:
            raise NotFoundError(
                "Room character not found",
                reason=ErrorReason.CHARACTER_NOT_FOUND,
                details={"room_character_id": room_character_id},
            )
        if game_role != GameRole.GM and entry.character.owner_id != user.id:
            raise ForbiddenError(
                "You do not have permission to remove this character",
                reason=ErrorReason.CHARACTER_PERMISSION_DENIED,
                details={"room_character_id": room_character_id},
            )
        deleted_token_ids = await self.tabletop_repo.delete_tokens_by_character(
            db,
            room_id=room_id,
            character_id=entry.character_id,
        )
        await self.repo.delete_by_id_and_room(
            db,
            room_character_id=room_character_id,
            room_id=room_id,
        )
        await db.commit()
        return deleted_token_ids

    async def set_visibility(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        room_character_id: int,
        user: User,
        payload: RoomCharacterVisibilityPatch,
    ) -> RoomCharacterEntryResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        if game_role != GameRole.GM:
            raise ForbiddenError(
                "Only GMs can manage character visibility",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"game_role": game_role},
            )
        existing = await self.repo.get_by_id_and_room(
            db,
            room_character_id=room_character_id,
            room_id=room_id,
        )
        if existing is None:
            raise NotFoundError(
                "Room character not found",
                reason=ErrorReason.CHARACTER_NOT_FOUND,
                details={"room_character_id": room_character_id},
            )
        await self.repo.set_visibility(
            db,
            room_character_id=room_character_id,
            is_hidden=payload.is_hidden,
        )
        await db.commit()
        updated = await self.repo.get_by_id_and_room(
            db,
            room_character_id=room_character_id,
            room_id=room_id,
        )
        assert updated is not None
        return self._entry_response(
            updated,
            updated.character.state,
            game_role=game_role,
            viewer_user_id=user.id,
        )

    async def set_data_visibility(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        room_character_id: int,
        user: User,
        payload: RoomCharacterDataVisibilityPatch,
    ) -> RoomCharacterEntryResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        if game_role != GameRole.GM:
            raise ForbiddenError(
                "Only GMs can manage character data visibility",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"game_role": game_role},
            )
        existing = await self.repo.get_by_id_and_room(
            db,
            room_character_id=room_character_id,
            room_id=room_id,
        )
        if existing is None:
            raise NotFoundError(
                "Room character not found",
                reason=ErrorReason.CHARACTER_NOT_FOUND,
                details={"room_character_id": room_character_id},
            )
        await self.repo.set_data_visibility(
            db,
            room_character_id=room_character_id,
            hide_data=payload.hide_data,
        )
        await db.commit()
        updated = await self.repo.get_by_id_and_room(
            db,
            room_character_id=room_character_id,
            room_id=room_id,
        )
        assert updated is not None
        return self._entry_response(
            updated,
            updated.character.state,
            game_role=game_role,
            viewer_user_id=user.id,
        )

    async def create_room_character(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        payload: RoomCharacterCreate,
        file: UploadFile | None = None,
    ) -> RoomCharacterEntryResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        require_game_permission(game_role, GamePermission.CREATE_CHARACTER_DEFINITION)

        token_image_asset_id = payload.token_image_asset_id
        if file is not None and file.filename:
            asset = await self.asset_service.create_image_asset(
                db,
                file=file,
                asset_type=AssetType.TOKEN_IMAGE,
                owner_id=user.id,
            )
            token_image_asset_id = asset.id

        if token_image_asset_id is None and payload.portrait_asset_id is not None:
            token_image_asset_id = payload.portrait_asset_id

        character = await self.character_service._create_character_record(
            db,
            owner_id=user.id,
            name=payload.name.strip(),
            player_name=payload.player_name,
            system=payload.system,
            portrait_asset_id=payload.portrait_asset_id,
            token_image_asset_id=token_image_asset_id,
            identity=payload.identity,
            flavor=payload.flavor,
            attributes=payload.attributes,
            features=payload.features,
            spells=payload.spells,
            resources=payload.resources,
            equipment=payload.equipment,
            extras=payload.extras,
        )
        state = await self.character_service._create_default_state(
            db,
            character_id=character.id,
            attributes=payload.attributes,
            explicit=payload.state,
        )
        panel: dict = {}
        if payload.state is not None:
            if payload.state.max_hp is not None:
                panel["hp_max"] = payload.state.max_hp
                panel["hp_current"] = payload.state.max_hp
            if payload.state.armor_class is not None:
                panel["ac"] = payload.state.armor_class
        primary_config = TokenConfigUpsert(
            is_primary=True,
            name=payload.name.strip(),
            asset_id=token_image_asset_id,
            panel_initial=panel,
            sort_order=0,
        )
        configs = await self.character_service._ensure_token_lib_resources(
            db,
            owner_id=user.id,
            character_name=payload.name.strip(),
            portrait_asset_id=payload.portrait_asset_id,
            configs=[primary_config],
        )
        _, added_lib_ids, _ = await self.character_service.token_config_repo.upsert_all(
            db,
            character_id=character.id,
            configs=configs,
        )
        for rid in added_lib_ids:
            await self.character_service.library_service.increment_usage(db, resource_id=rid)
        await self.repo.create(
            db,
            room_id=room_id,
            character_id=character.id,
            added_by_user_id=user.id,
        )
        await db.commit()

        created = await self.repo.get_by_room_and_character(
            db,
            room_id=room_id,
            character_id=character.id,
        )
        if created is None:
            raise BadRequestError(
                "Failed to create room character",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                details={"character_id": character.id, "room_id": room_id},
            )
        return self._entry_response(
            created,
            created.character.state or state,
            game_role=game_role,
            viewer_user_id=user.id,
        )

    async def link_room_character(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        character_id: int,
    ) -> RoomCharacterEntryResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        require_game_permission(game_role, GamePermission.CREATE_CHARACTER_DEFINITION)

        character = await self.character_service._get_or_404(
            db,
            character_id=character_id,
        )
        if character.owner_id != user.id:
            raise ForbiddenError(
                "You do not have permission to link this character",
                reason=ErrorReason.CHARACTER_PERMISSION_DENIED,
                details={"character_id": character_id},
            )

        existing = await self.repo.get_by_room_and_character(
            db,
            room_id=room_id,
            character_id=character_id,
        )
        if existing is not None:
            return self._entry_response(
                existing,
                existing.character.state,
                game_role=game_role,
                viewer_user_id=user.id,
            )

        state = await self.character_service.state_repo.get_by_character_id(
            db,
            character_id=character_id,
        )
        if state is None:
            state = await self.character_service._create_default_state(
                db,
                character_id=character_id,
                attributes=character.attributes,
            )

        entry = await self.repo.create(
            db,
            room_id=room_id,
            character_id=character_id,
            added_by_user_id=user.id,
        )
        await db.commit()

        linked = await self.repo.get_by_room_and_character(
            db,
            room_id=room_id,
            character_id=character_id,
        )
        if linked is None:
            raise BadRequestError(
                "Failed to link character to room",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                details={"character_id": character_id, "room_id": room_id},
            )
        return self._entry_response(
            linked,
            linked.character.state or state,
            game_role=game_role,
            viewer_user_id=user.id,
        )

    @staticmethod
    def parse_room_character_create(
        *,
        name: str,
        player_name: str = "",
        system: str = "dnd5e",
        portrait_asset_id: int | None = None,
        token_image_asset_id: int | None = None,
        identity_json: str | None = None,
        flavor_json: str | None = None,
        attributes_json: str | None = None,
        features_json: str | None = None,
        spells_json: str | None = None,
        resources_json: str | None = None,
        equipment_json: str | None = None,
        extras_json: str | None = None,
        state_json: str | None = None,
    ) -> RoomCharacterCreate:
        name = name.strip()
        if not name:
            raise BadRequestError(
                "Character name is required",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
            )

        def parse_json(label: str, raw: str | None) -> dict[str, Any] | None:
            if raw is None or raw == "":
                return None
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise BadRequestError(
                    f"Invalid {label} JSON",
                    reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                ) from exc
            if not isinstance(parsed, dict):
                raise BadRequestError(
                    f"Invalid {label} JSON",
                    reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                )
            return parsed

        def parse_json_list(label: str, raw: str | None) -> list[dict[str, Any]] | None:
            if raw is None or raw == "":
                return None
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise BadRequestError(
                    f"Invalid {label} JSON",
                    reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                ) from exc
            if not isinstance(parsed, list):
                raise BadRequestError(
                    f"Invalid {label} JSON",
                    reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                )
            return [item for item in parsed if isinstance(item, dict)]

        spells_raw = parse_json("spells", spells_json)
        state_raw = parse_json("state", state_json)
        state = CharacterStateCreate.model_validate(state_raw) if state_raw else None
        resources_raw = parse_json_list("resources", resources_json)

        return RoomCharacterCreate(
            name=name,
            player_name=player_name,
            system=system,
            portrait_asset_id=portrait_asset_id,
            token_image_asset_id=token_image_asset_id,
            identity=parse_json("identity", identity_json) or {},
            flavor=parse_json("flavor", flavor_json) or {},
            attributes=parse_json("attributes", attributes_json) or {},
            features=parse_json("features", features_json) or {},
            spells=spells_raw,
            resources=resources_raw or [],
            equipment=parse_json("equipment", equipment_json) or {},
            extras=parse_json("extras", extras_json) or {},
            state=state,
        )
