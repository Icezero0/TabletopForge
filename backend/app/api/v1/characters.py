from fastapi import APIRouter, Depends, Query
from fastapi import Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_realtime_publisher
from app.core.database import get_db
from app.modules.auth.deps import get_current_user
from app.modules.character.schemas import (
    CharacterCreate,
    CharacterListResponse,
    CharacterPatch,
    CharacterResponse,
    CharacterStatePatch,
    CharacterStateResponse,
)
from app.modules.character.service import CharacterService
from app.modules.rooms.characters.repository import RoomCharacterRepository
from app.modules.rooms.tabletop.service import RoomTabletopService
from app.modules.users.models import User
from app.realtime.publisher import RealtimePublisher

router = APIRouter(prefix="/characters", tags=["characters"])

character_service = CharacterService()
room_character_repo = RoomCharacterRepository()
tabletop_service = RoomTabletopService()


@router.get("", response_model=CharacterListResponse)
async def list_characters(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterListResponse:
    return await character_service.list_characters(
        db, user=current_user, page=page, page_size=page_size
    )


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    payload: CharacterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterResponse:
    data = payload.model_dump()
    state = data.pop("state", None)
    kind = data.get("kind")
    if kind is not None:
        data["kind"] = kind.value if hasattr(kind, "value") else kind
    character = await character_service.create_character(
        db,
        user=current_user,
        state=state,
        **data,
    )
    return CharacterResponse.model_validate(character)


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterResponse:
    character = await character_service.get_character(
        db, character_id=character_id, user=current_user
    )
    return CharacterResponse.model_validate(character)


@router.patch("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: int,
    payload: CharacterPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterResponse:
    patch_fields = {
        k: v for k, v in payload.model_dump().items() if k in payload.model_fields_set
    }
    if "kind" in patch_fields and patch_fields["kind"] is not None:
        patch_fields["kind"] = patch_fields["kind"].value
    character = await character_service.update_character(
        db, character_id=character_id, user=current_user, patch_fields=patch_fields
    )
    return CharacterResponse.model_validate(character)


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    await character_service.delete_character(
        db, character_id=character_id, user=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{character_id}/state", response_model=CharacterStateResponse)
async def get_character_state(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CharacterStateResponse:
    return await character_service.get_character_state(
        db,
        character_id=character_id,
        user=current_user,
    )


@router.patch("/{character_id}/state", response_model=CharacterStateResponse)
async def patch_character_state(
    character_id: int,
    payload: CharacterStatePatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> CharacterStateResponse:
    patch_fields = {
        k: v for k, v in payload.model_dump().items() if k in payload.model_fields_set
    }
    state = await character_service.patch_character_state(
        db,
        character_id=character_id,
        user=current_user,
        patch_fields=patch_fields,
    )
    broadcast = await tabletop_service.build_character_state_broadcast(
        db,
        character_id=character_id,
    )
    if broadcast is not None and broadcast.get("state_summary") is not None:
        room_ids = await room_character_repo.list_room_ids_for_character(
            db,
            character_id=character_id,
        )
        for room_id in room_ids:
            await publisher.publish_character_state_updated(
                room_id=room_id,
                character_id=character_id,
                state_summary=broadcast["state_summary"],
                state_summary_public=broadcast.get("state_summary_public"),
            )
    return state
