from enum import StrEnum


class RoomRole(StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    MEMBER = "member"


class GameRole(StrEnum):
    GM = "GM"
    PL = "PL"
    OB = "OB"


class GamePermission(StrEnum):
    UPLOAD_MAP = "upload_map"
    DELETE_MAP = "delete_map"
    LOCK_MAP = "lock_map"
    MOVE_UNLOCKED_MAP = "move_unlocked_map"
    MANAGE_DRAWINGS = "manage_drawings"
    ERASE_DRAWINGS = "erase_drawings"
    MANAGE_ANY_TOKEN = "manage_any_token"
    MOVE_ANY_TOKEN = "move_any_token"
    MOVE_OWN_CHARACTER_TOKEN = "move_own_character_token"
    VIEW_MONSTER_EXACT_HP = "view_monster_exact_hp"
    VIEW_MONSTER_DAMAGE_LOG = "view_monster_damage_log"
    EDIT_ANY_CHARACTER = "edit_any_character"
    EDIT_OWN_CHARACTER = "edit_own_character"
    EDIT_ANY_CHARACTER_STATE = "edit_any_character_state"
    EDIT_OWN_CHARACTER_STATE = "edit_own_character_state"
    CREATE_CHARACTER_DEFINITION = "create_character_definition"
    REUSE_CHARACTER_DEFINITION = "reuse_character_definition"
    PAN_ZOOM_TABLE = "pan_zoom_table"


class RoomPermission(StrEnum):
    VIEW_ROOM = "view_room"
    UPDATE_ROOM = "update_room"
    DELETE_ROOM = "delete_room"
    VIEW_MEMBERS = "view_members"
    INVITE_USER = "invite_user"
    REVIEW_JOIN_REQUEST = "review_join_request"
    MANAGE_MEMBERS = "manage_members"
    MANAGE_MANAGERS = "manage_managers"
    VIEW_MESSAGES = "view_messages"
    SEND_MESSAGE = "send_message"


class RoomVisibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"


class RoomJoinAuditMode(StrEnum):
    AUTO_APPROVE = "auto_approve"
    MANUAL_REVIEW = "manual_review"
    AUTO_REJECT = "auto_reject"


class RoomJoinRequestSource(StrEnum):
    APPLY = "apply"
    INVITE = "invite"
    MEMBER_INVITE = "member_invite"


class RoomJoinRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class RoomJoinRequestAction(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RoomJoinRequestListScope(StrEnum):
    HANDLED_BY_ME = "handled_by_me"
    CREATED_BY_ME = "created_by_me"
    ALL_RELATED_TO_ME = "all_related_to_me"
