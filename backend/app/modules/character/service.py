from math import ceil
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.character.attributes import derived_int
from app.modules.character.constants import (
    CharacterKind,
    assert_global_character_kind,
    kind_value,
)
from app.modules.character.models import Character, CharacterState
from app.modules.character.presenter import present_character_state
from app.modules.character.repository import CharacterRepository
from app.modules.character.schemas import (
    CharacterListResponse,
    CharacterResponse,
    CharacterStateCreate,
    CharacterStatePatch,
    CharacterStateResponse,
    TokenConfigUpsert,
)
from app.modules.character.state_repository import CharacterStateRepository
from app.modules.character.token_config_repository import TokenConfigRepository
from app.modules.library.constants import ResourceType
from app.modules.library.service import LibraryService
from app.modules.rooms.characters.repository import RoomCharacterRepository
from app.modules.rooms.constants import GamePermission, GameRole
from app.modules.rooms.game_permissions import require_game_permission
from app.modules.rooms.membership.repository import RoomMembershipRepository
from app.modules.users.models import User


class CharacterService:
    def __init__(self) -> None:
        self.repo = CharacterRepository()
        self.state_repo = CharacterStateRepository()
        self.token_config_repo = TokenConfigRepository()
        self.library_service = LibraryService()
        self.room_character_repo = RoomCharacterRepository()
        self.membership_repo = RoomMembershipRepository()

    async def _ensure_token_lib_resources(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        character_name: str,
        portrait_asset_id: int | None,
        configs: list[TokenConfigUpsert],
    ) -> list[TokenConfigUpsert]:
        """Ensure every token config has a library_resource_id.

        For configs that already have one, nothing changes.
        For configs without one, auto-create a library token resource:
          - image source: cfg.asset_id first; for primary configs fall back to portrait.
          - name: cfg.name if set, otherwise character_name.
        """
        result: list[TokenConfigUpsert] = []
        for cfg in configs:
            if cfg.library_resource_id is None:
                source_asset_id = cfg.asset_id
                if source_asset_id is None and cfg.is_primary:
                    source_asset_id = portrait_asset_id
                if source_asset_id is not None:
                    resource = await self.library_service.create_resource_from_asset_id(
                        db,
                        owner_id=owner_id,
                        type=ResourceType.TOKEN,
                        name=cfg.name or character_name,
                        asset_id=source_asset_id,
                    )
                    cfg = cfg.model_copy(update={"library_resource_id": resource.id})
            result.append(cfg)
        return result

    def _require_owner(self, character: Character, user: User) -> None:
        if character.owner_id != user.id:
            raise ForbiddenError(
                "You do not have permission to access this character",
                reason=ErrorReason.CHARACTER_PERMISSION_DENIED,
                details={"character_id": character.id},
            )

    async def _get_or_404(self, db: AsyncSession, *, character_id: int) -> Character:
        character = await self.repo.get_by_id(db, character_id=character_id)
        if character is None:
            raise NotFoundError(
                "Character not found",
                reason=ErrorReason.CHARACTER_NOT_FOUND,
                details={"character_id": character_id},
            )
        return character

    async def _create_character_record(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        name: str,
        player_name: str = "",
        kind: str = CharacterKind.PC_MAIN.value,
        system: str = "dnd5e",
        portrait_asset_id: int | None = None,
        token_image_asset_id: int | None = None,
        identity: dict | None = None,
        flavor: dict | None = None,
        attributes: dict | None = None,
        features: dict | None = None,
        spells: dict | None = None,
        equipment: dict | None = None,
        extras: dict | None = None,
    ) -> Character:
        return await self.repo.create(
            db,
            owner_id=owner_id,
            name=name,
            player_name=player_name,
            kind=kind,
            system=system,
            portrait_asset_id=portrait_asset_id,
            token_image_asset_id=token_image_asset_id,
            identity=identity,
            flavor=flavor,
            attributes=attributes,
            features=features,
            spells=spells,
            equipment=equipment,
            extras=extras,
        )

    async def _create_default_state(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        attributes: dict | None = None,
        explicit: CharacterStateCreate | None = None,
    ) -> CharacterState:
        max_hp = explicit.max_hp if explicit else None
        current_hp = explicit.current_hp if explicit else None
        armor_class = explicit.armor_class if explicit else None
        temp_hp = explicit.temp_hp if explicit else 0
        conditions = explicit.conditions if explicit else {}

        if max_hp is None:
            max_hp = derived_int(attributes, "max_hp")
        if armor_class is None:
            armor_class = derived_int(attributes, "ac")
        if current_hp is None and max_hp is not None:
            current_hp = max_hp

        return await self.state_repo.create(
            db,
            character_id=character_id,
            current_hp=current_hp,
            max_hp=max_hp,
            temp_hp=temp_hp,
            armor_class=armor_class,
            conditions=conditions,
        )

    async def create_character(
        self,
        db: AsyncSession,
        *,
        user: User,
        name: str,
        player_name: str = "",
        kind: str = CharacterKind.PC_MAIN.value,
        system: str = "dnd5e",
        portrait_asset_id: int | None = None,
        token_image_asset_id: int | None = None,
        identity: dict | None = None,
        flavor: dict | None = None,
        attributes: dict | None = None,
        features: dict | None = None,
        spells: dict | None = None,
        equipment: dict | None = None,
        extras: dict | None = None,
        token_configs: list[TokenConfigUpsert] | None = None,
        state: CharacterStateCreate | None = None,
    ) -> Character:
        user_is_gm = await self.membership_repo.user_is_gm_in_any_room(
            db,
            user_id=user.id,
        )
        assert_global_character_kind(kind_value(kind), user_is_gm=user_is_gm)

        character = await self._create_character_record(
            db,
            owner_id=user.id,
            name=name,
            player_name=player_name,
            kind=kind,
            system=system,
            portrait_asset_id=portrait_asset_id,
            token_image_asset_id=token_image_asset_id,
            identity=identity,
            flavor=flavor,
            attributes=attributes,
            features=features,
            spells=spells,
            equipment=equipment,
            extras=extras,
        )
        await self._create_default_state(
            db,
            character_id=character.id,
            attributes=attributes,
            explicit=state,
        )
        if token_configs:
            token_configs = await self._ensure_token_lib_resources(
                db,
                owner_id=user.id,
                character_name=name,
                portrait_asset_id=portrait_asset_id,
                configs=token_configs,
            )
            _, added_lib_ids, removed_lib_ids = await self.token_config_repo.upsert_all(
                db,
                character_id=character.id,
                configs=token_configs,
            )
            for rid in added_lib_ids:
                await self.library_service.increment_usage(db, resource_id=rid)
            for rid in removed_lib_ids:
                await self.library_service.decrement_usage(db, resource_id=rid)
        await db.commit()
        # Reload with token_configs eager-loaded
        refreshed = await self.repo.get_by_id(db, character_id=character.id)
        return refreshed or character

    async def get_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
    ) -> Character:
        character, _ = await self.require_character_accessible(
            db,
            character_id=character_id,
            user=user,
            read_only=True,
        )
        return character

    async def list_characters(
        self,
        db: AsyncSession,
        *,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> CharacterListResponse:
        offset = (page - 1) * page_size
        items, total = await self.repo.list_by_owner(
            db,
            owner_id=user.id,
            offset=offset,
            limit=page_size,
        )
        return CharacterListResponse(
            items=[CharacterResponse.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total else 0,
        )

    def _require_stable_layer_write(
        self,
        character: Character,
        user: User,
        game_role: GameRole | None,
    ) -> None:
        if character.owner_id != user.id:
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.CHARACTER_PERMISSION_DENIED,
                details={"character_id": character.id},
            )
        require_game_permission(
            game_role or GameRole.PL,
            GamePermission.EDIT_OWN_CHARACTER,
        )

    async def update_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
        patch_fields: dict,
    ) -> Character:
        character, game_role = await self.require_character_accessible(
            db,
            character_id=character_id,
            user=user,
        )
        self._require_stable_layer_write(character, user, game_role)

        token_configs: list[TokenConfigUpsert] | None = patch_fields.pop("token_configs", None)
        updated = await self.repo.update(db, character=character, **patch_fields)

        if token_configs is not None:
            token_configs = await self._ensure_token_lib_resources(
                db,
                owner_id=user.id,
                character_name=updated.name,
                portrait_asset_id=updated.portrait_asset_id,
                configs=token_configs,
            )
            _, added_lib_ids, removed_lib_ids = await self.token_config_repo.upsert_all(
                db,
                character_id=character_id,
                configs=token_configs,
            )
            for rid in added_lib_ids:
                await self.library_service.increment_usage(db, resource_id=rid)
            for rid in removed_lib_ids:
                await self.library_service.decrement_usage(db, resource_id=rid)

        await db.commit()
        # Reload with token_configs eager-loaded
        refreshed = await self.repo.get_by_id(db, character_id=character_id)
        return refreshed or updated

    async def delete_character(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
    ) -> None:
        character = await self._get_or_404(db, character_id=character_id)
        self._require_owner(character, user)
        await self.repo.delete(db, character=character)
        await db.commit()

    async def get_character_internal(
        self,
        db: AsyncSession,
        *,
        character_id: int,
    ) -> Character:
        return await self._get_or_404(db, character_id=character_id)

    async def require_character_accessible(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
        read_only: bool = False,
    ) -> tuple[Character, GameRole | None]:
        character = await self._get_or_404(db, character_id=character_id)
        if character.owner_id == user.id:
            return character, None

        game_role = await self.room_character_repo.user_game_role_for_character(
            db,
            character_id=character_id,
            user_id=user.id,
        )
        if game_role is None:
            raise ForbiddenError(
                "You do not have permission to access this character",
                reason=ErrorReason.CHARACTER_PERMISSION_DENIED,
                details={"character_id": character_id},
            )
        return character, game_role

    def _require_state_write(
        self,
        character: Character,
        user: User,
        game_role: GameRole | None,
    ) -> None:
        if character.owner_id == user.id:
            require_game_permission(game_role or GameRole.PL, GamePermission.EDIT_OWN_CHARACTER_STATE)
            return
        if game_role == GameRole.GM:
            require_game_permission(game_role, GamePermission.EDIT_ANY_CHARACTER_STATE)
            return
        raise ForbiddenError(
            "You do not have permission to perform this action",
            reason=ErrorReason.CHARACTER_PERMISSION_DENIED,
            details={"character_id": character.id},
        )

    async def get_character_state(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
    ) -> CharacterStateResponse:
        character, game_role = await self.require_character_accessible(
            db,
            character_id=character_id,
            user=user,
            read_only=True,
        )
        state = await self.state_repo.get_by_character_id(db, character_id=character_id)
        if state is None:
            raise NotFoundError(
                "Character state not found",
                reason=ErrorReason.CHARACTER_NOT_FOUND,
                details={"character_id": character_id},
            )
        return present_character_state(
            character,
            state,
            game_role=game_role,
            viewer_user_id=user.id,
        )

    async def patch_character_state(
        self,
        db: AsyncSession,
        *,
        character_id: int,
        user: User,
        patch_fields: dict,
    ) -> CharacterStateResponse:
        character, game_role = await self.require_character_accessible(
            db,
            character_id=character_id,
            user=user,
        )
        self._require_state_write(character, user, game_role)

        state = await self.state_repo.get_by_character_id(db, character_id=character_id)
        if state is None:
            raise NotFoundError(
                "Character state not found",
                reason=ErrorReason.CHARACTER_NOT_FOUND,
                details={"character_id": character_id},
            )

        patch_fields = dict(patch_fields)
        if "current_hp" in patch_fields:
            can_track_damage = game_role == GameRole.GM or (
                character.owner_id == user.id
                and character.kind == CharacterKind.NPC.value
            )
            if can_track_damage:
                old_hp = state.current_hp or 0
                new_hp = patch_fields["current_hp"]
                if new_hp is not None and new_hp < old_hp:
                    delta = new_hp - old_hp
                    patch_fields["damage_taken"] = state.damage_taken + abs(delta)
                    conditions = dict(state.conditions or {})
                    log = list(conditions.get("damage_log") or [])
                    log.append({
                        "delta": delta,
                        "at": datetime.now(UTC).isoformat(),
                    })
                    conditions["damage_log"] = log
                    patch_fields["conditions"] = conditions

        updated = await self.state_repo.update(db, state=state, **patch_fields)
        await db.commit()
        return present_character_state(
            character,
            updated,
            game_role=game_role,
            viewer_user_id=user.id,
        )
