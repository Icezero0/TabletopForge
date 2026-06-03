from fastapi import Request

from app.realtime.manager import RealtimeManager
from app.realtime.publisher import RealtimePublisher
from app.realtime.room_presence import RoomPresenceService


def get_realtime_manager(request: Request) -> RealtimeManager:
    return request.app.state.realtime_manager


def get_realtime_publisher(request: Request) -> RealtimePublisher:
    return request.app.state.realtime_publisher


def get_realtime_room_presence_service(request: Request) -> RoomPresenceService:
    return request.app.state.realtime_room_presence_service

