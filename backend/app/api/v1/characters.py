from fastapi import APIRouter, Depends, Query
from fastapi import Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.deps import get_current_user
from app.modules.character.schemas import (
    CharacterCreate,
    CharacterListResponse,
    CharacterPatch,
    CharacterResponse,
)
from app.modules.character.service import CharacterService
from app.modules.users.models import User

router = APIRouter(prefix="/characters", tags=["characters"])

character_service = CharacterService()


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
    character = await character_service.create_character(
        db,
        user=current_user,
        **payload.model_dump(),
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
    # Only update fields that were explicitly included in the request body.
    # This lets clients send null to clear nullable fields (portrait_asset_id, spells)
    # without affecting fields they didn't mention.
    patch_fields = {
        k: v for k, v in payload.model_dump().items() if k in payload.model_fields_set
    }
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
