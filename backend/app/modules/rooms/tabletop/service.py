from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.modules.assets.constants import AssetType
from app.modules.assets.service import AssetService
from app.modules.character.models import Character
from app.modules.character.presenter import build_character_state_broadcast
from app.modules.character.repository import CharacterRepository
from app.modules.character.state_repository import CharacterStateRepository
from app.modules.library.constants import ResourceType
from app.modules.library.repository import LibraryRepository
from app.modules.library.service import LibraryService
from app.modules.rooms.characters.repository import RoomCharacterRepository
from app.modules.rooms.constants import GamePermission, GameRole
from app.modules.rooms.game_permissions import require_game_permission
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.models import RoomDrawing, RoomMap, RoomTabletopSettings, RoomToken
from app.modules.rooms.room.service import RoomService
from app.modules.rooms.tabletop.repository import RoomTabletopRepository
from app.modules.rooms.tabletop.schemas import (
    RoomDrawingCreate,
    RoomDrawingPatch,
    RoomDrawingResponse,
    RoomCombatState,
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

ABILITY_KEYS = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")
SKILL_KEYS = (
    "acrobatics",
    "animal_handling",
    "arcana",
    "athletics",
    "deception",
    "history",
    "insight",
    "intimidation",
    "investigation",
    "medicine",
    "nature",
    "perception",
    "performance",
    "persuasion",
    "religion",
    "sleight_of_hand",
    "stealth",
    "survival",
)


class RoomTabletopService:
    def __init__(self) -> None:
        self.repo = RoomTabletopRepository()
        self.membership_service = RoomMembershipService()
        self.room_service = RoomService()
        self.asset_service = AssetService()
        self.library_repo = LibraryRepository()
        self.library_service = LibraryService()
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

    @staticmethod
    def _panel_without_deprecated_fields(panel: dict | None) -> dict | None:
        if not panel:
            return panel
        cleaned = dict(panel)
        cleaned.pop("damage_taken", None)
        return cleaned

    @staticmethod
    def _panel_int(value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return int(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _build_panel_state_summary(
        token: RoomToken,
        *,
        game_role: GameRole,
    ) -> TokenStateSummary | None:
        panel = token.panel
        if not panel:
            return None
        current_hp = panel.get("hp_current")
        max_hp = panel.get("hp_max")
        ac = panel.get("ac")
        pp = panel.get("pp")
        current_hp_int = RoomTabletopService._panel_int(current_hp)
        max_hp_int = RoomTabletopService._panel_int(max_hp)
        damage_taken = (
            max(0, max_hp_int - current_hp_int)
            if current_hp_int is not None and max_hp_int is not None
            else None
        )
        if game_role != GameRole.GM and panel.get("hide_hp") is True:
            current_hp = None
            max_hp = None
        if all(v is None for v in (current_hp, max_hp, ac, pp, damage_taken)):
            return None
        return TokenStateSummary(
            current_hp=current_hp,
            max_hp=max_hp,
            ac=ac,
            pp=pp,
            damage_taken=damage_taken,
        )

    @staticmethod
    def _build_spawn_panel_from_config(panel_initial: dict | None) -> dict:
        panel = dict(panel_initial or {})
        panel.pop("damage_taken", None)
        resources = panel.get("resources")
        if not isinstance(resources, list):
            return panel

        normalized_resources: list[dict] = []
        for resource in resources:
            if not isinstance(resource, dict):
                continue
            max_value = resource.get("max", 0)
            try:
                max_count = max(0, int(max_value))
            except (TypeError, ValueError):
                max_count = 0

            current_value = resource.get("current", max_count)
            try:
                current_count = int(current_value)
            except (TypeError, ValueError):
                current_count = max_count
            current_count = min(max(current_count, 0), max_count)

            normalized_resources.append(
                {
                    **resource,
                    "max": max_count,
                    "current": current_count,
                }
            )

        panel["resources"] = normalized_resources
        return panel

    @staticmethod
    def _build_primary_panel_from_character(character: Character) -> dict:
        attributes = character.attributes or {}
        features = character.features or {}
        spells = character.spells or {}
        equipment = character.equipment or {}
        resources = character.resources or []

        def parse_num(value: object) -> int | None:
            if isinstance(value, dict):
                value = value.get("value")
            try:
                if value is None or str(value).strip() == "":
                    return None
                return int(float(str(value).strip()))
            except (TypeError, ValueError):
                return None

        def is_auto(raw: object, flag: object) -> bool:
            if isinstance(flag, bool):
                return flag
            return str(raw or "").strip() == ""

        ability_scores = dict(attributes.get("ability_scores") or {})
        derived = dict(attributes.get("derived") or {})
        save_values = dict(attributes.get("saving_throws") or {})
        save_autos = dict(attributes.get("saving_throw_autos") or {})
        save_profs = dict(attributes.get("saving_throw_profs") or {})
        skill_values = dict(attributes.get("skill_values") or {})
        skill_autos = dict(attributes.get("skill_value_autos") or {})
        skill_profs = dict(attributes.get("skill_profs") or {})

        saving_throws: dict[str, int | None] = {}
        for key in ABILITY_KEYS:
            raw = save_values.get(key)
            override = parse_num(raw)
            saving_throws[key] = override if not is_auto(raw, save_autos.get(key)) and override is not None else None

        skills: dict[str, int | None] = {}
        for key in SKILL_KEYS:
            raw = skill_values.get(key)
            override = parse_num(raw)
            skills[key] = override if not is_auto(raw, skill_autos.get(key)) and override is not None else None

        return {
            "ability_scores": ability_scores,
            "ac": parse_num(derived.get("ac")),
            "hp_current": parse_num(derived.get("max_hp")),
            "hp_max": parse_num(derived.get("max_hp")),
            "initiative": parse_num(derived.get("initiative")),
            "speed": parse_num(derived.get("speed")),
            "pp": parse_num(derived.get("passive_perception")),
            "proficiency_bonus": parse_num(derived.get("proficiency_bonus")) or 2,
            "saving_throws": saving_throws,
            "saving_throw_profs": save_profs,
            "skills": skills,
            "skill_profs": skill_profs,
            "racial_traits": list(features.get("racial_traits") or []),
            "feats": list(features.get("feats") or []),
            "class_features": list(features.get("class_features") or []),
            "items": list((equipment.get("items") if isinstance(equipment, dict) else []) or []),
            "weapons": [],
            "armor": [],
            "spellcasting_ability": spells.get("spellcasting_ability") or "intelligence",
            "spell_save_dc": {
                "value": parse_num((spells.get("spell_save_dc") or {}).get("value") if isinstance(spells.get("spell_save_dc"), dict) else None) or 0,
                "breakdown": "",
            },
            "spell_attack_bonus": {
                "value": parse_num((spells.get("spell_attack_bonus") or {}).get("value") if isinstance(spells.get("spell_attack_bonus"), dict) else None) or 0,
                "breakdown": "",
            },
            "spellbook": dict(spells.get("spellbook") or {}),
            "resources": list(resources),
            "inherit_items_from_character": True,
        }

    async def _ensure_character_primary_token_resource(
        self,
        db: AsyncSession,
        *,
        character: Character,
    ) -> int:
        asset_id = character.token_image_asset_id or character.portrait_asset_id
        resource = None
        if character.primary_token_resource_id is not None:
            resource = await self.library_repo.get_by_id(
                db,
                resource_id=character.primary_token_resource_id,
            )
        if resource is None:
            resource = await self.library_service.create_resource_from_asset_id(
                db,
                owner_id=character.owner_id,
                type=ResourceType.TOKEN,
                name=character.name,
                asset_id=asset_id,
            )
            resource.meta = {
                **(resource.meta or {}),
                "generated_from": "character_primary_token",
                "character_id": character.id,
            }
            character.primary_token_resource_id = resource.id
            await db.flush()
            await self.library_service.increment_usage(db, resource_id=resource.id)
            return resource.id

        await self.library_service.sync_character_primary_token_resource(
            db,
            resource=resource,
            character_id=character.id,
            name=character.name,
            asset_id=asset_id,
        )
        return resource.id

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
        room_id = tokens[0].room_id
        hidden_ids = await self.room_character_repo.get_hidden_character_ids_for_room(
            db, room_id=room_id
        )
        character_ids = [
            t.linked_character_id for t in tokens if t.linked_character_id is not None
        ]
        characters = await self.character_repo.get_by_ids(db, character_ids=character_ids)
        responses: list[RoomTokenResponse] = []
        for token in tokens:
            character = (
                characters.get(token.linked_character_id)
                if token.linked_character_id is not None
                else None
            )
            character_hidden = (
                token.linked_character_id is not None
                and token.linked_character_id in hidden_ids
            )
            base = RoomTokenResponse.model_validate(token)
            state_summary = self._build_panel_state_summary(token, game_role=game_role)
            updates: dict = {
                "panel": self._panel_without_deprecated_fields(token.panel),
                "state_summary": state_summary,
                "character_hidden": character_hidden,
            }
            if character is not None:
                updates["linked_character_owner_id"] = character.owner_id
            responses.append(base.model_copy(update=updates))
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
            maps=[RoomMapResponse.from_orm(m) for m in maps],
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
        settings = await self._get_or_create_settings(db, room_id=room_id)
        settings_fields = {"grid_cell_ft", "grid_cell_px"}
        changes_settings = bool(settings_fields & payload.model_fields_set)
        changes_combat = "combat_state" in payload.model_fields_set
        changes_music = "music_state" in payload.model_fields_set
        changes_fog = "fog_state" in payload.model_fields_set

        if game_role != GameRole.GM and (changes_settings or changes_music or changes_fog):
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"game_role": game_role},
            )
        if game_role != GameRole.GM and changes_combat:
            await self._require_combat_state_update_access(
                db,
                room_id=room_id,
                user=user,
                current_state=RoomCombatState.model_validate(settings.combat_state)
                if settings.combat_state is not None
                else None,
                next_state=payload.combat_state,
            )

        updated = await self.repo.update_settings(
            db,
            settings=settings,
            grid_cell_ft=payload.grid_cell_ft,
            grid_cell_px=payload.grid_cell_px,
            combat_state=(
                payload.combat_state.model_dump(mode="json")
                if payload.combat_state is not None
                else None
            ),
            combat_state_provided="combat_state" in payload.model_fields_set,
            music_state=(
                payload.music_state.model_dump(mode="json")
                if payload.music_state is not None
                else None
            ),
            music_state_provided="music_state" in payload.model_fields_set,
            fog_state=(
                payload.fog_state.model_dump(mode="json")
                if payload.fog_state is not None
                else None
            ),
            fog_state_provided="fog_state" in payload.model_fields_set,
        )
        await db.commit()
        return RoomTabletopSettingsResponse.model_validate(updated)

    async def _require_combat_state_update_access(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        current_state: RoomCombatState | None,
        next_state: RoomCombatState | None,
    ) -> None:
        if not self._is_player_end_turn_update(current_state, next_state):
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"room_id": room_id},
            )

        assert current_state is not None
        ordered = sorted(current_state.combatants, key=lambda item: item.turn_order)
        current_combatant = ordered[current_state.turn_index]
        token = await self.repo.get_token(
            db,
            room_id=room_id,
            token_id=current_combatant.token_id,
        )
        if token is None or token.linked_character_id is None:
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"room_id": room_id, "token_id": current_combatant.token_id},
            )
        character = await self.character_repo.get_by_id(
            db,
            character_id=token.linked_character_id,
        )
        if character is None or character.owner_id != user.id:
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"room_id": room_id, "token_id": current_combatant.token_id},
            )

    def _is_player_end_turn_update(
        self,
        current_state: RoomCombatState | None,
        next_state: RoomCombatState | None,
    ) -> bool:
        if current_state is None or next_state is None:
            return False
        if not current_state.active or not next_state.active:
            return False
        if current_state.combatants != next_state.combatants:
            return False

        ordered = sorted(current_state.combatants, key=lambda item: item.turn_order)
        if not ordered or current_state.turn_index >= len(ordered):
            return False
        current = ordered[current_state.turn_index]
        if current.ready_round > current_state.round:
            return False

        next_round = current_state.round
        next_turn_index: int | None = None
        for index in range(current_state.turn_index + 1, len(ordered)):
            if ordered[index].ready_round <= current_state.round:
                next_turn_index = index
                break
        if next_turn_index is None:
            next_round = current_state.round + 1
            next_turn_index = next(
                (index for index, combatant in enumerate(ordered) if combatant.ready_round <= next_round),
                None,
            )
        if next_turn_index is None:
            return False

        return next_state.round == next_round and next_state.turn_index == next_turn_index

    async def create_map(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        file: UploadFile,
        name: str | None = None,
        comment: str | None = None,
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
        resource_name = name.strip() if name and name.strip() else file.filename or asset.filename
        resource_meta = {}
        if comment and comment.strip():
            resource_meta["comment"] = comment.strip()
        resource = await self.library_repo.create(
            db,
            owner_id=user.id,
            type=ResourceType.MAP_BACKGROUND,
            name=resource_name,
            primary_asset_id=asset.id,
            meta=resource_meta,
        )
        resource.usage_count = 1
        await db.flush()

        room_map = await self.repo.create_map(
            db,
            room_id=room_id,
            library_resource_id=resource.id,
            x=x,
            y=y,
            scale=scale,
            z_index=next_z_index,
        )
        await db.commit()
        return RoomMapResponse.from_orm(room_map)

    async def create_map_from_resource(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        resource_id: int,
        x: float = 0.0,
        y: float = 0.0,
        scale: float = 1.0,
    ) -> RoomMapResponse:
        game_role = await self._require_member_game_role(db, room_id=room_id, user=user)
        require_game_permission(game_role, GamePermission.UPLOAD_MAP)

        resource = await self.library_repo.get_by_id(db, resource_id=resource_id)
        if resource is None:
            raise NotFoundError(
                "Library resource not found",
                reason=ErrorReason.ROOM_NOT_FOUND,
                details={"resource_id": resource_id},
            )
        if resource.owner_id != user.id:
            raise ForbiddenError(
                "You do not have permission to use this resource",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"resource_id": resource_id},
            )

        existing_maps = await self.repo.list_maps(db, room_id=room_id)
        next_z_index = (
            max((m.z_index for m in existing_maps), default=-1) + 1
            if existing_maps
            else 0
        )

        await self.library_repo.adjust_usage_count(db, resource=resource, delta=1)
        room_map = await self.repo.create_map(
            db,
            room_id=room_id,
            library_resource_id=resource.id,
            x=x,
            y=y,
            scale=scale,
            z_index=next_z_index,
        )
        await db.commit()
        return RoomMapResponse.from_orm(room_map)

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
            scale_x=payload.scale_x,
            scale_y=payload.scale_y,
            _scale_x_set="scale_x" in payload.model_fields_set,
            _scale_y_set="scale_y" in payload.model_fields_set,
            locked=payload.locked,
            z_index=payload.z_index,
        )
        await db.commit()
        return RoomMapResponse.from_orm(updated)

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
        library_resource = room_map.library_resource
        await self.repo.delete_map(db, room_map=room_map)
        settings = await self.repo.get_settings(db, room_id=room_id)
        if settings is not None and settings.fog_state:
            fog_maps = dict((settings.fog_state or {}).get("maps") or {})
            if str(map_id) in fog_maps:
                fog_maps.pop(str(map_id), None)
                settings.fog_state = {
                    **settings.fog_state,
                    "maps": fog_maps,
                }
        await self.library_repo.adjust_usage_count(db, resource=library_resource, delta=-1)
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
        linked_character_id: int,
        library_resource_id: int | None = None,
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

        await self._validate_linked_character_in_room(
            db,
            room_id=room_id,
            character_id=linked_character_id,
        )
        if library_resource_id is not None:
            resource = await self.library_repo.get_by_id(
                db,
                resource_id=library_resource_id,
            )
            if resource is None:
                raise NotFoundError(
                    "Library resource not found",
                    reason=ErrorReason.ROOM_NOT_FOUND,
                    details={"resource_id": library_resource_id},
                )
            if resource.owner_id != user.id:
                raise ForbiddenError(
                    "You do not have permission to use this resource",
                    reason=ErrorReason.ROOM_PERMISSION_DENIED,
                    details={"resource_id": library_resource_id},
                )
            if resource.type != ResourceType.TOKEN.value:
                raise BadRequestError(
                    "Library resource is not a token",
                    reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                    details={"resource_id": library_resource_id, "type": resource.type},
                )

        settings = await self._get_or_create_settings(db, room_id=room_id)
        existing_tokens = await self.repo.list_tokens(db, room_id=room_id)
        next_z_index = max((t.z_index for t in existing_tokens), default=-1) + 1

        token = await self.repo.create_token(
            db,
            room_id=room_id,
            name=name,
            x=x,
            y=y,
            width=settings.grid_cell_ft,
            height=settings.grid_cell_ft,
            owner_user_id=user.id,
            linked_character_id=linked_character_id,
            library_resource_id=library_resource_id,
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

        selected_config = None
        if payload.token_config_id is not None:
            selected_config = next(
                (cfg for cfg in (character.token_configs or []) if cfg.id == payload.token_config_id),
                None,
            )

        spawn_library_resource_id = selected_config.library_resource_id if selected_config else None
        if selected_config is None:
            spawn_library_resource_id = await self._ensure_character_primary_token_resource(
                db,
                character=character,
            )

        spawn_name = (
            payload.name
            or (selected_config.name if selected_config and selected_config.name else None)
            or character.name
        ).strip()

        if not spawn_name:
            raise BadRequestError(
                "Token name is required",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
            )

        spawn_panel_source = (
            selected_config.panel_initial
            if selected_config
            else self._build_primary_panel_from_character(character)
        )
        spawn_panel = self._build_spawn_panel_from_config(spawn_panel_source)

        token = await self.repo.create_token(
            db,
            room_id=room_id,
            name=spawn_name,
            x=payload.x if payload.x is not None else 0.0,
            y=payload.y if payload.y is not None else 0.0,
            width=settings.grid_cell_ft,
            height=settings.grid_cell_ft,
            owner_user_id=user.id,
            linked_character_id=character_id,
            library_resource_id=spawn_library_resource_id,
            z_index=next_z_index,
            panel=spawn_panel,
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
        if linked_character_id_set:
            if payload.linked_character_id is None:
                raise BadRequestError(
                    "linked_character_id cannot be null",
                    reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                    details={"token_id": token_id},
                )
            await self._validate_linked_character_in_room(
                db,
                room_id=room_id,
                character_id=payload.linked_character_id,
            )

        panel_merge = self._panel_without_deprecated_fields(payload.panel)

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
            panel_merge=panel_merge,
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

