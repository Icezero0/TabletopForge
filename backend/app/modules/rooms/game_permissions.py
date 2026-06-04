from app.core.error_reasons import ErrorReason
from app.core.exceptions import ForbiddenError
from app.modules.rooms.constants import GamePermission, GameRole

ROLE_PERMISSIONS: dict[GameRole, set[GamePermission]] = {
    GameRole.GM: {
        GamePermission.UPLOAD_MAP,
        GamePermission.DELETE_MAP,
        GamePermission.LOCK_MAP,
        GamePermission.MOVE_UNLOCKED_MAP,
        GamePermission.MANAGE_DRAWINGS,
        GamePermission.ERASE_DRAWINGS,
        GamePermission.MANAGE_ANY_TOKEN,
        GamePermission.MOVE_ANY_TOKEN,
        GamePermission.MOVE_OWN_CHARACTER_TOKEN,
        GamePermission.VIEW_MONSTER_EXACT_HP,
        GamePermission.VIEW_MONSTER_DAMAGE_LOG,
        GamePermission.EDIT_ANY_CHARACTER,
        GamePermission.EDIT_OWN_CHARACTER,
        GamePermission.EDIT_ANY_CHARACTER_STATE,
        GamePermission.EDIT_OWN_CHARACTER_STATE,
        GamePermission.CREATE_CHARACTER_DEFINITION,
        GamePermission.REUSE_CHARACTER_DEFINITION,
        GamePermission.PAN_ZOOM_TABLE,
    },
    GameRole.PL: {
        GamePermission.MANAGE_DRAWINGS,
        GamePermission.ERASE_DRAWINGS,
        GamePermission.MOVE_OWN_CHARACTER_TOKEN,
        GamePermission.VIEW_MONSTER_DAMAGE_LOG,
        GamePermission.EDIT_OWN_CHARACTER,
        GamePermission.EDIT_OWN_CHARACTER_STATE,
        GamePermission.CREATE_CHARACTER_DEFINITION,
        GamePermission.REUSE_CHARACTER_DEFINITION,
        GamePermission.PAN_ZOOM_TABLE,
    },
    GameRole.OB: {
        GamePermission.VIEW_MONSTER_DAMAGE_LOG,
        GamePermission.PAN_ZOOM_TABLE,
    },
}


def get_permissions_by_game_role(role: GameRole) -> set[GamePermission]:
    return ROLE_PERMISSIONS.get(role, set())


def has_game_permission(role: GameRole, permission: GamePermission) -> bool:
    return permission in get_permissions_by_game_role(role)


def require_game_permission(role: GameRole, permission: GamePermission) -> None:
    if not has_game_permission(role, permission):
        raise ForbiddenError(
            "You do not have permission to perform this action",
            reason=ErrorReason.ROOM_PERMISSION_DENIED,
            details={"game_role": role, "permission": permission},
        )
