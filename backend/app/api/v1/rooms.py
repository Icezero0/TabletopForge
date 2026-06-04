from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_realtime_manager,
    get_realtime_publisher,
    get_realtime_room_presence_service,
)
from app.core.database import get_db
from app.modules.auth.deps import get_current_user
from app.modules.rooms.constants import (
    RoomJoinRequestSource,
    RoomJoinRequestStatus,
    RoomPermission,
)
from app.modules.rooms.join_request.schemas import (
    RoomJoinRequestCreate,
    RoomJoinRequestListResponse,
    RoomJoinRequestResponse,
)
from app.modules.rooms.join_request.service import RoomJoinRequestService
from app.modules.rooms.membership.schemas import (
    RoomMemberGameRolePatch,
    RoomMemberListResponse,
    RoomMemberResponse,
)
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.personal_memo.schemas import (
    RoomPersonalMemoPut,
    RoomPersonalMemoResponse,
)
from app.modules.rooms.personal_memo.service import RoomPersonalMemoService
from app.modules.rooms.room.schemas import (
    RoomCreate,
    RoomListResponse,
    RoomPatch,
    RoomResponse,
)
from app.modules.rooms.room.service import RoomService
from app.modules.rooms.permissions import has_room_permission
from app.modules.users.models import User
from app.realtime.constants import SessionCloseReason
from app.realtime.manager import RealtimeManager
from app.realtime.publisher import RealtimePublisher
from app.realtime.rest_sync import close_room_sessions, close_room_user_session
from app.realtime.room_presence import RoomPresenceService

router = APIRouter(prefix="/rooms", tags=["rooms"])

room_service = RoomService()
membership_service = RoomMembershipService()
join_request_service = RoomJoinRequestService()
personal_memo_service = RoomPersonalMemoService()


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    payload: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomResponse:
    room = await room_service.create_room(db, user=current_user, payload=payload)
    return RoomResponse.model_validate(room)


@router.get("", response_model=RoomListResponse)
async def get_rooms(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    name: str | None = Query(default=None),
    owner_username: str | None = Query(default=None),
    owner_email: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomListResponse:
    data = await room_service.get_rooms(
        db,
        page=page,
        page_size=page_size,
        name=name,
        owner_username=owner_username,
        owner_email=owner_email,
    )
    return RoomListResponse(
        items=[RoomResponse.model_validate(room) for room in data["items"]],
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
        total_pages=data["total_pages"],
    )


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomResponse:
    room = await room_service.get_accessible_room_by_id(
        db,
        room_id=room_id,
        user=current_user,
    )
    return RoomResponse.model_validate(room)


@router.patch("/{room_id}", response_model=RoomResponse)
async def patch_room(
    room_id: int,
    payload: RoomPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomResponse:
    room = await room_service.patch_room(
        db,
        room_id=room_id,
        user=current_user,
        payload=payload,
    )
    await publisher.publish_room_info(room_id=room_id)
    return RoomResponse.model_validate(room)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    manager: RealtimeManager = Depends(get_realtime_manager),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
    presence_service: RoomPresenceService = Depends(get_realtime_room_presence_service),
) -> Response:
    await room_service.delete_room(db, room_id=room_id, user=current_user)
    await close_room_sessions(
        manager=manager,
        publisher=publisher,
        presence_service=presence_service,
        room_id=room_id,
        reason=SessionCloseReason.ROOM_DELETED,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{room_id}/members", response_model=RoomMemberListResponse)
async def get_room_members(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomMemberListResponse:
    await room_service.get_room_by_id(db, room_id)

    data = await membership_service.get_room_members(
        db,
        room_id=room_id,
        user=current_user,
    )
    return RoomMemberListResponse(
        items=[RoomMemberResponse.model_validate(member) for member in data["items"]],
        total=data["total"],
    )


@router.get("/{room_id}/personal-memo", response_model=RoomPersonalMemoResponse)
async def get_room_personal_memo(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomPersonalMemoResponse:
    memo = await personal_memo_service.get_personal_memo(
        db,
        room_id=room_id,
        user=current_user,
    )
    return RoomPersonalMemoResponse.model_validate(memo)


@router.put("/{room_id}/personal-memo", response_model=RoomPersonalMemoResponse)
async def put_room_personal_memo(
    room_id: int,
    payload: RoomPersonalMemoPut,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomPersonalMemoResponse:
    memo = await personal_memo_service.put_personal_memo(
        db,
        room_id=room_id,
        user=current_user,
        content=payload.content,
    )
    return RoomPersonalMemoResponse.model_validate(memo)


@router.get("/{room_id}/join-requests", response_model=RoomJoinRequestListResponse)
async def get_room_join_requests(
    room_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_: RoomJoinRequestStatus | None = Query(default=None, alias="status"),
    source: RoomJoinRequestSource | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomJoinRequestListResponse:
    data = await join_request_service.get_room_join_requests(
        db,
        room_id=room_id,
        user=current_user,
        page=page,
        page_size=page_size,
        status=status_,
        source=source,
    )
    return RoomJoinRequestListResponse(
        items=[RoomJoinRequestResponse.model_validate(item) for item in data["items"]],
        total=data["total"],
        page=data["page"],
        page_size=data["page_size"],
        total_pages=data["total_pages"],
    )


@router.post(
    "/{room_id}/join-requests/apply",
    status_code=status.HTTP_200_OK,
)
async def apply_room_join_request(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> None:
    request = await join_request_service.create_apply_request(
        db,
        room_id=room_id,
        user=current_user,
    )
    if request is None:
        await publisher.publish_room_members(room_id=room_id)
        return

    reviewer_user_ids = await membership_service.get_room_user_ids_by_permission(
        db,
        room_id=room_id,
        permission=RoomPermission.REVIEW_JOIN_REQUEST,
    )
    for reviewer_user_id in reviewer_user_ids:
        if reviewer_user_id == current_user.id:
            continue
        await publisher.publish_notification(user_id=reviewer_user_id)


@router.post(
    "/{room_id}/join-requests/invite",
    status_code=status.HTTP_200_OK,
)
async def invite_room_join_request(
    room_id: int,
    payload: RoomJoinRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> None:
    await join_request_service.create_invite_request(
        db,
        room_id=room_id,
        target_user_id=payload.target_user_id,
        user=current_user,
    )
    await publisher.publish_notification(user_id=payload.target_user_id)

    role = await membership_service.find_room_role(
        db,
        room_id=room_id,
        user_id=current_user.id,
    )
    can_review = (
        role is not None
        and has_room_permission(role=role, permission=RoomPermission.REVIEW_JOIN_REQUEST)
    )
    if can_review:
        return

    reviewer_user_ids = await membership_service.get_room_user_ids_by_permission(
        db,
        room_id=room_id,
        permission=RoomPermission.REVIEW_JOIN_REQUEST,
    )
    for reviewer_user_id in reviewer_user_ids:
        if reviewer_user_id == current_user.id:
            continue
        await publisher.publish_notification(user_id=reviewer_user_id)


@router.delete(
    "/{room_id}/members/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def leave_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    manager: RealtimeManager = Depends(get_realtime_manager),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
    presence_service: RoomPresenceService = Depends(get_realtime_room_presence_service),
) -> Response:
    await membership_service.leave_room(
        db,
        room_id=room_id,
        user=current_user,
    )
    await close_room_user_session(
        manager=manager,
        publisher=publisher,
        presence_service=presence_service,
        room_id=room_id,
        user_id=current_user.id,
        reason=SessionCloseReason.LEFT_ROOM,
    )
    await publisher.publish_room_members(room_id=room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{room_id}/members/{target_user_id}/manager",
    response_model=RoomMemberResponse,
)
async def set_room_member_manager(
    room_id: int,
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomMemberResponse:
    member = await membership_service.set_room_member_manager_status(
        db,
        room_id=room_id,
        target_user_id=target_user_id,
        is_manager=True,
        current_user=current_user,
    )
    await publisher.publish_room_members(room_id=room_id)
    return RoomMemberResponse.model_validate(member)


@router.delete(
    "/{room_id}/members/{target_user_id}/manager",
    response_model=RoomMemberResponse,
)
async def unset_room_member_manager(
    room_id: int,
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomMemberResponse:
    member = await membership_service.set_room_member_manager_status(
        db,
        room_id=room_id,
        target_user_id=target_user_id,
        is_manager=False,
        current_user=current_user,
    )
    await publisher.publish_room_members(room_id=room_id)
    return RoomMemberResponse.model_validate(member)


@router.patch(
    "/{room_id}/members/{target_user_id}/game-role",
    response_model=RoomMemberResponse,
)
async def patch_room_member_game_role(
    room_id: int,
    target_user_id: int,
    payload: RoomMemberGameRolePatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomMemberResponse:
    member = await membership_service.set_room_member_game_role(
        db,
        room_id=room_id,
        target_user_id=target_user_id,
        game_role=payload.game_role,
        current_user=current_user,
    )
    await publisher.publish_room_members(room_id=room_id)
    return RoomMemberResponse.model_validate(member)


@router.delete(
    "/{room_id}/members/{target_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_room_member(
    room_id: int,
    target_user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    manager: RealtimeManager = Depends(get_realtime_manager),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
    presence_service: RoomPresenceService = Depends(get_realtime_room_presence_service),
) -> Response:
    await membership_service.remove_room_member(
        db,
        room_id=room_id,
        target_user_id=target_user_id,
        current_user=current_user,
    )
    await close_room_user_session(
        manager=manager,
        publisher=publisher,
        presence_service=presence_service,
        room_id=room_id,
        user_id=target_user_id,
        reason=SessionCloseReason.REMOVED_FROM_ROOM,
    )
    await publisher.publish_room_members(room_id=room_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
