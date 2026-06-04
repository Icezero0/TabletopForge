from enum import StrEnum


class WsMessageType(StrEnum):
    AUTH = "auth"
    HEARTBEAT = "heartbeat"
    COMMAND = "command"
    EVENT = "event"
    ERROR = "error"
    ACK = "ack"


class WsHeartbeatAction(StrEnum):
    PING = "ping"
    PONG = "pong"


class WsCommandAction(StrEnum):
    ROOM_ENTER = "room_enter"
    ROOM_LEAVE = "room_leave"
    ROOM_PRESENCE_GET = "room_presence_get"
    POINTER_PRESENCE = "pointer_presence"
    POINTER_LASER = "pointer_laser"


class WsEventType(StrEnum):
    NOTIFICATION = "notification"

    ROOM_INFO = "room_info"
    ROOM_MEMBERS = "room_members"

    ROOM_USER_PRESENCE = "room_user_presence"
    SESSION_CLOSED = "session_closed"

    MESSAGE = "message"

    TABLETOP_SETTINGS_UPDATED = "tabletop_settings_updated"
    MAP_CREATED = "map_created"
    MAP_UPDATED = "map_updated"
    MAP_DELETED = "map_deleted"
    DRAWING_CREATED = "drawing_created"
    DRAWING_UPDATED = "drawing_updated"
    DRAWING_DELETED = "drawing_deleted"
    POINTER_PRESENCE = "pointer_presence"
    POINTER_LASER = "pointer_laser"


class WsErrorCode(StrEnum):
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    BAD_REQUEST = "bad_request"
    INVALID_PAYLOAD = "invalid_payload"
    INTERNAL_ERROR = "internal_error"


class SessionCloseReason(StrEnum):
    ENTERED_ELSEWHERE = "entered_elsewhere"
    LEFT_ROOM = "left_room"
    REMOVED_FROM_ROOM = "removed_from_room"
    ROOM_DELETED = "room_deleted"


class ChannelKind(StrEnum):
    USER = "user"
    ROOM = "room"


