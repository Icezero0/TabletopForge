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


class WsEventType(StrEnum):
    NOTIFICATION = "notification"

    ROOM_INFO = "room_info"
    ROOM_SETTINGS = "room_settings"
    ROOM_MEMBERS = "room_members"

    ROOM_USER_PRESENCE = "room_user_presence"
    SESSION_CLOSED = "session_closed"

    MESSAGE = "message"


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


