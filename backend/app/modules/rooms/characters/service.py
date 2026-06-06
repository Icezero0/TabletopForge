import json
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError
from app.modules.assets.constants import AssetType
from app.modules.assets.service import AssetService
from app.modules.character.constants import CharacterKind
from app.modules.character.models import CharacterState
from app.modules.character.presenter import present_character_state_summary
from app.modules.character.schemas import CharacterStateCreate
from app.modules.character.service import CharacterService
from app.modules.rooms.characters.repository import RoomCharacterRepository
from app.modules.rooms.characters.schemas import RoomCharacterCreate, RoomCharacterEntryResponse
from app.modules.rooms.constants import GamePermission, GameRole
from app.modules.rooms.game_permissions import require_game_permission
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.models import RoomCharacter
from app.modules.rooms.room.service import RoomService
from app.modules.users.models import User


class RoomCharacterService:
    def __init__(self) -> None:
        self.repo = RoomCharacterRepository()
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
        owner_is_gm_in_room: bool,
    ) -> RoomCharacterEntryResponse:
        character = entry.character
        state_summary = present_character_state_summary(
            character,
            state,
            game_role=game_role,
            viewer_user_id=viewer_user_id,
            owner_is_gm_in_room=owner_is_gm_in_room,
        )
        return RoomCharacterEntryResponse(
            room_character_id=entry.id,
            character_id=character.id,
            owner_id=character.owner_id,
            kind=entry.kind,
            name=character.name,
            player_name=character.player_name,
            token_image_asset_id=character.token_image_asset_id,
            state=state_summary,
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
        responses: list[RoomCharacterEntryResponse] = []
        for entry in entries:
            owner_is_gm = await self.repo.is_owner_gm_in_room(
                db,
                room_id=room_id,
                owner_id=entry.character.owner_id,
            )
            responses.append(
                self._entry_response(
                    entry,
                    entry.character.state,
                    game_role=game_role,
                    viewer_user_id=user.id,
                    owner_is_gm_in_room=owner_is_gm,
                )
            )
        return responses

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

        kind_value = payload.kind.value if isinstance(payload.kind, CharacterKind) else payload.kind

        if kind_value == CharacterKind.MONSTER.value:
            raise BadRequestError(
                "Character kind 'monster' is not supported",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                details={"kind": kind_value},
            )

        character = await self.character_service._create_character_record(
            db,
            owner_id=user.id,
            name=payload.name.strip(),
            player_name=payload.player_name,
            kind=kind_value,
            system=payload.system,
            portrait_asset_id=payload.portrait_asset_id,
            token_image_asset_id=token_image_asset_id,
            identity=payload.identity,
            flavor=payload.flavor,
            attributes=payload.attributes,
            features=payload.features,
            spells=payload.spells,
            equipment=payload.equipment,
            extras=payload.extras,
        )
        state = await self.character_service._create_default_state(
            db,
            character_id=character.id,
            attributes=payload.attributes,
            explicit=payload.state,
        )
        entry = await self.repo.create(
            db,
            room_id=room_id,
            character_id=character.id,
            kind=kind_value,
            added_by_user_id=user.id,
        )
        await db.commit()
        await db.refresh(character)
        owner_is_gm = await self.repo.is_owner_gm_in_room(
            db,
            room_id=room_id,
            owner_id=character.owner_id,
        )
        return self._entry_response(
            entry,
            state,
            game_role=game_role,
            viewer_user_id=user.id,
            owner_is_gm_in_room=owner_is_gm,
        )

    @staticmethod
    def parse_room_character_create(
        *,
        kind: str,
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

        try:
            kind_enum = CharacterKind(kind)
        except ValueError as exc:
            raise BadRequestError(
                "Invalid character kind",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                details={"kind": kind},
            ) from exc

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

        spells_raw = parse_json("spells", spells_json)
        state_raw = parse_json("state", state_json)
        state = CharacterStateCreate.model_validate(state_raw) if state_raw else None

        return RoomCharacterCreate(
            name=name,
            player_name=player_name,
            kind=kind_enum,
            system=system,
            portrait_asset_id=portrait_asset_id,
            token_image_asset_id=token_image_asset_id,
            identity=parse_json("identity", identity_json) or {},
            flavor=parse_json("flavor", flavor_json) or {},
            attributes=parse_json("attributes", attributes_json) or {},
            features=parse_json("features", features_json) or {},
            spells=spells_raw,
            equipment=parse_json("equipment", equipment_json) or {},
            extras=parse_json("extras", extras_json) or {},
            state=state,
        )
