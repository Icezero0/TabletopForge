from enum import StrEnum

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError
from app.modules.rooms.constants import GameRole


class CharacterKind(StrEnum):
    PC_MAIN = "pc_main"
    PC_ADDITIONAL = "pc_additional"
    NPC = "npc"


def kind_value(kind: CharacterKind | str) -> str:
    return kind.value if isinstance(kind, CharacterKind) else kind


def assert_room_character_kind(game_role: GameRole, kind: CharacterKind | str) -> None:
    value = kind_value(kind)
    if game_role == GameRole.GM:
        allowed = {CharacterKind.NPC.value}
    elif game_role == GameRole.PL:
        allowed = {CharacterKind.PC_MAIN.value, CharacterKind.PC_ADDITIONAL.value}
    else:
        raise BadRequestError(
            "Invalid character kind for role",
            reason=ErrorReason.REQUEST_VALIDATION_FAILED,
            details={"kind": value, "game_role": game_role.value},
        )
    if value not in allowed:
        raise BadRequestError(
            "Invalid character kind for role",
            reason=ErrorReason.REQUEST_VALIDATION_FAILED,
            details={"kind": value, "game_role": game_role.value},
        )


def assert_global_character_kind(kind: CharacterKind | str, *, user_is_gm: bool) -> None:
    value = kind_value(kind)
    if value == CharacterKind.NPC.value:
        if not user_is_gm:
            raise BadRequestError(
                "Only GMs can create NPC characters",
                reason=ErrorReason.REQUEST_VALIDATION_FAILED,
                details={"kind": value},
            )
        return
    if value in {CharacterKind.PC_MAIN.value, CharacterKind.PC_ADDITIONAL.value}:
        return
    raise BadRequestError(
        "Invalid character kind",
        reason=ErrorReason.REQUEST_VALIDATION_FAILED,
        details={"kind": value},
    )
