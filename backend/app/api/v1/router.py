from fastapi import APIRouter

from app.api.v1 import assets, auth, feedback, library, messages, notifications, room_join_request, rooms, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(assets.router)
api_router.include_router(users.router)
api_router.include_router(rooms.router)
api_router.include_router(notifications.router)
api_router.include_router(room_join_request.router)
api_router.include_router(messages.router)
api_router.include_router(feedback.router)
api_router.include_router(library.router)
