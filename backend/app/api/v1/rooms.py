from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
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
    RoomMemberPlayerColorPatch,
    RoomMemberResponse,
)
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.personal_memo.schemas import (
    RoomPersonalMemoPut,
    RoomPersonalMemoResponse,
)
from app.modules.rooms.personal_memo.service import RoomPersonalMemoService
from app.modules.rooms.tabletop.schemas import (
    RoomDrawingCreate,
    RoomDrawingPatch,
    RoomDrawingResponse,
    RoomDrawingsBulkDelete,
    RoomMapPatch,
    RoomMapResponse,
    RoomTabletopSettingsPatch,
    RoomTabletopSettingsResponse,
    RoomTabletopSnapshotResponse,
    RoomTokenPatch,
    RoomTokenResponse,
    SpawnCharacterTokenRequest,
)
from app.modules.rooms.tabletop.service import RoomTabletopService
from app.modules.rooms.characters.schemas import (
    RoomCharacterEntryResponse,
    RoomCharacterLinkRequest,
    RoomCharacterVisibilityPatch,
)
from app.modules.rooms.characters.service import RoomCharacterService
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
tabletop_service = RoomTabletopService()
room_characters_service = RoomCharacterService()


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
    await db.commit()
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


@router.get("/{room_id}/tabletop", response_model=RoomTabletopSnapshotResponse)
async def get_room_tabletop(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomTabletopSnapshotResponse:
    return await tabletop_service.get_snapshot(
        db,
        room_id=room_id,
        user=current_user,
    )


@router.patch(
    "/{room_id}/tabletop/settings",
    response_model=RoomTabletopSettingsResponse,
)
async def patch_room_tabletop_settings(
    room_id: int,
    payload: RoomTabletopSettingsPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomTabletopSettingsResponse:
    settings = await tabletop_service.patch_settings(
        db,
        room_id=room_id,
        user=current_user,
        payload=payload,
    )
    await publisher.publish_tabletop_settings_updated(
        room_id=room_id,
        settings=settings.model_dump(mode="json"),
    )
    return settings


@router.post(
    "/{room_id}/maps",
    response_model=RoomMapResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room_map(
    room_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomMapResponse:
    room_map = await tabletop_service.create_map(
        db,
        room_id=room_id,
        user=current_user,
        file=file,
    )
    await publisher.publish_map_created(
        room_id=room_id,
        map_data=room_map.model_dump(mode="json"),
    )
    return room_map


@router.patch("/{room_id}/maps/{map_id}", response_model=RoomMapResponse)
async def patch_room_map(
    room_id: int,
    map_id: int,
    payload: RoomMapPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomMapResponse:
    room_map = await tabletop_service.patch_map(
        db,
        room_id=room_id,
        map_id=map_id,
        user=current_user,
        payload=payload,
    )
    await publisher.publish_map_updated(
        room_id=room_id,
        map_data=room_map.model_dump(mode="json"),
    )
    return room_map


@router.delete("/{room_id}/maps/{map_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room_map(
    room_id: int,
    map_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> Response:
    await tabletop_service.delete_map(
        db,
        room_id=room_id,
        map_id=map_id,
        user=current_user,
    )
    await publisher.publish_map_deleted(room_id=room_id, map_id=map_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{room_id}/drawings",
    response_model=RoomDrawingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room_drawing(
    room_id: int,
    payload: RoomDrawingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomDrawingResponse:
    drawing = await tabletop_service.create_drawing(
        db,
        room_id=room_id,
        user=current_user,
        payload=payload,
    )
    await publisher.publish_drawing_created(
        room_id=room_id,
        drawing=drawing.model_dump(mode="json"),
    )
    return drawing


@router.patch(
    "/{room_id}/drawings/{drawing_id}",
    response_model=RoomDrawingResponse,
)
async def patch_room_drawing(
    room_id: int,
    drawing_id: int,
    payload: RoomDrawingPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomDrawingResponse:
    drawing = await tabletop_service.patch_drawing(
        db,
        room_id=room_id,
        drawing_id=drawing_id,
        user=current_user,
        payload=payload,
    )
    await publisher.publish_drawing_updated(
        room_id=room_id,
        drawing=drawing.model_dump(mode="json"),
    )
    return drawing


@router.delete("/{room_id}/drawings", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room_drawings(
    room_id: int,
    payload: RoomDrawingsBulkDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> Response:
    deleted_ids = await tabletop_service.delete_drawings(
        db,
        room_id=room_id,
        user=current_user,
        drawing_ids=payload.ids,
    )
    if deleted_ids:
        await publisher.publish_drawing_deleted(
            room_id=room_id,
            drawing_ids=deleted_ids,
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{room_id}/tokens",
    response_model=RoomTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room_token(
    room_id: int,
    name: str = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    linked_character_id: int | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomTokenResponse:
    token = await tabletop_service.create_token(
        db,
        room_id=room_id,
        user=current_user,
        name=name,
        x=x,
        y=y,
        file=file,
        linked_character_id=linked_character_id,
    )
    await publisher.publish_token_created(
        room_id=room_id,
        token=token.model_dump(mode="json"),
    )
    return token


@router.patch("/{room_id}/tokens/{token_id}", response_model=RoomTokenResponse)
async def patch_room_token(
    room_id: int,
    token_id: int,
    payload: RoomTokenPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomTokenResponse:
    token = await tabletop_service.patch_token(
        db,
        room_id=room_id,
        token_id=token_id,
        user=current_user,
        payload=payload,
    )
    await publisher.publish_token_updated(
        room_id=room_id,
        token=token.model_dump(mode="json"),
    )
    return token


@router.delete("/{room_id}/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room_token(
    room_id: int,
    token_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> Response:
    await tabletop_service.delete_token(
        db,
        room_id=room_id,
        token_id=token_id,
        user=current_user,
    )
    await publisher.publish_token_deleted(room_id=room_id, token_id=token_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{room_id}/characters", response_model=list[RoomCharacterEntryResponse])
async def get_room_characters(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RoomCharacterEntryResponse]:
    return await room_characters_service.list_room_characters(
        db,
        room_id=room_id,
        user=current_user,
    )


@router.post(
    "/{room_id}/characters",
    response_model=RoomCharacterEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room_character(
    room_id: int,
    kind: str = Form(...),
    name: str = Form(...),
    player_name: str = Form(""),
    system: str = Form("dnd5e"),
    portrait_asset_id: int | None = Form(None),
    token_image_asset_id: int | None = Form(None),
    identity_json: str | None = Form(None),
    flavor_json: str | None = Form(None),
    attributes_json: str | None = Form(None),
    features_json: str | None = Form(None),
    spells_json: str | None = Form(None),
    equipment_json: str | None = Form(None),
    extras_json: str | None = Form(None),
    state_json: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomCharacterEntryResponse:
    payload = RoomCharacterService.parse_room_character_create(
        kind=kind,
        name=name,
        player_name=player_name,
        system=system,
        portrait_asset_id=portrait_asset_id,
        token_image_asset_id=token_image_asset_id,
        identity_json=identity_json,
        flavor_json=flavor_json,
        attributes_json=attributes_json,
        features_json=features_json,
        spells_json=spells_json,
        equipment_json=equipment_json,
        extras_json=extras_json,
        state_json=state_json,
    )
    return await room_characters_service.create_room_character(
        db,
        room_id=room_id,
        user=current_user,
        payload=payload,
        file=file,
    )


@router.post(
    "/{room_id}/characters/link",
    response_model=RoomCharacterEntryResponse,
)
async def link_room_character(
    room_id: int,
    payload: RoomCharacterLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomCharacterEntryResponse:
    return await room_characters_service.link_room_character(
        db,
        room_id=room_id,
        user=current_user,
        character_id=payload.character_id,
    )


@router.delete(
    "/{room_id}/characters/{room_character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_room_character(
    room_id: int,
    room_character_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await room_characters_service.remove_room_character(
        db,
        room_id=room_id,
        room_character_id=room_character_id,
        user=current_user,
    )


@router.patch(
    "/{room_id}/characters/{room_character_id}/visibility",
    response_model=RoomCharacterEntryResponse,
)
async def patch_room_character_visibility(
    room_id: int,
    room_character_id: int,
    payload: RoomCharacterVisibilityPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RoomCharacterEntryResponse:
    return await room_characters_service.set_visibility(
        db,
        room_id=room_id,
        room_character_id=room_character_id,
        user=current_user,
        payload=payload,
    )


@router.post(
    "/{room_id}/characters/{character_id}/spawn-token",
    response_model=RoomTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def spawn_room_character_token(
    room_id: int,
    character_id: int,
    payload: SpawnCharacterTokenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomTokenResponse:
    token = await tabletop_service.spawn_character_token(
        db,
        room_id=room_id,
        character_id=character_id,
        user=current_user,
        payload=payload,
    )
    await publisher.publish_token_created(
        room_id=room_id,
        token=token.model_dump(mode="json"),
    )
    return token


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
    "/{room_id}/members/me/player-color",
    response_model=RoomMemberResponse,
)
async def patch_my_player_color(
    room_id: int,
    payload: RoomMemberPlayerColorPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> RoomMemberResponse:
    member = await membership_service.patch_my_player_color(
        db,
        room_id=room_id,
        user=current_user,
        player_color=payload.player_color,
    )
    await db.commit()
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
