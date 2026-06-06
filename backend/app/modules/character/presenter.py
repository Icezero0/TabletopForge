from typing import Any

from app.modules.character.attributes import derived_int
from app.modules.character.constants import CharacterKind
from app.modules.character.models import Character, CharacterState
from app.modules.character.schemas import CharacterStateResponse, CharacterStateSummary
from app.modules.rooms.constants import GamePermission, GameRole
from app.modules.rooms.game_permissions import has_game_permission
from app.modules.rooms.tabletop.schemas import TokenStateSummary


def _can_view_exact_hp(game_role: GameRole | None) -> bool:
    if game_role is None:
        return False
    return has_game_permission(game_role, GamePermission.VIEW_MONSTER_EXACT_HP)


def viewer_sees_exact_hp(
    character: Character,
    *,
    game_role: GameRole | None,
    viewer_user_id: int | None,
) -> bool:
    if viewer_user_id is not None and character.owner_id == viewer_user_id:
        return True
    if _can_view_exact_hp(game_role):
        return True
    if character.kind == CharacterKind.NPC.value:
        return False
    return True


def _filtered_conditions(state: CharacterState, *, exact_hp: bool) -> dict[str, Any]:
    conditions = dict(state.conditions or {})
    if exact_hp:
        return conditions
    damage_log = conditions.get("damage_log")
    if damage_log is None:
        return {}
    return {"damage_log": damage_log}


def present_character_state(
    character: Character,
    state: CharacterState,
    *,
    game_role: GameRole | None,
    viewer_user_id: int | None,
) -> CharacterStateResponse:
    exact_hp = viewer_sees_exact_hp(
        character,
        game_role=game_role,
        viewer_user_id=viewer_user_id,
    )
    if not exact_hp:
        conditions = _filtered_conditions(state, exact_hp=False)
        return CharacterStateResponse(
            character_id=state.character_id,
            current_hp=None,
            max_hp=None,
            temp_hp=state.temp_hp,
            armor_class=None,
            conditions=conditions,
            damage_taken=state.damage_taken,
            updated_at=state.updated_at,
        )
    return CharacterStateResponse.model_validate(state)


def present_character_state_summary(
    character: Character,
    state: CharacterState | None,
    *,
    game_role: GameRole | None,
    viewer_user_id: int | None,
) -> CharacterStateSummary:
    if state is None:
        return CharacterStateSummary(
            current_hp=None,
            max_hp=None,
            armor_class=None,
            damage_taken=None,
        )
    exact_hp = viewer_sees_exact_hp(
        character,
        game_role=game_role,
        viewer_user_id=viewer_user_id,
    )
    if not exact_hp:
        return CharacterStateSummary(
            current_hp=None,
            max_hp=None,
            armor_class=None,
            damage_taken=state.damage_taken,
        )
    return CharacterStateSummary(
        current_hp=state.current_hp,
        max_hp=state.max_hp,
        armor_class=state.armor_class,
        damage_taken=state.damage_taken,
    )


def present_token_state_summary(
    character: Character,
    state: CharacterState | None,
    *,
    game_role: GameRole | None,
    viewer_user_id: int | None,
) -> TokenStateSummary:
    if state is None:
        return TokenStateSummary(
            current_hp=None,
            max_hp=None,
            ac=None,
            pp=None,
            damage_taken=None,
        )
    exact_hp = viewer_sees_exact_hp(
        character,
        game_role=game_role,
        viewer_user_id=viewer_user_id,
    )
    if not exact_hp:
        return TokenStateSummary(
            current_hp=None,
            max_hp=None,
            ac=None,
            pp=None,
            damage_taken=state.damage_taken,
        )
    return TokenStateSummary(
        current_hp=state.current_hp,
        max_hp=state.max_hp,
        ac=state.armor_class,
        pp=derived_int(character.attributes, "passive_perception"),
        damage_taken=state.damage_taken,
    )


def build_character_state_broadcast(
    character: Character,
    state: CharacterState | None,
) -> dict[str, Any]:
    if state is None:
        return {
            "state_summary": None,
            "state_summary_public": None,
        }
    gm_summary = present_token_state_summary(
        character,
        state,
        game_role=GameRole.GM,
        viewer_user_id=character.owner_id,
    )
    is_npc = character.kind == CharacterKind.NPC.value
    if is_npc:
        public_summary = present_token_state_summary(
            character,
            state,
            game_role=GameRole.PL,
            viewer_user_id=None,
        )
    else:
        public_summary = gm_summary
    result: dict[str, Any] = {
        "state_summary": gm_summary.model_dump(mode="json"),
    }
    if is_npc:
        result["state_summary_public"] = public_summary.model_dump(mode="json")
    return result
