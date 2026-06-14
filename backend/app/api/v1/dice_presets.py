from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.deps import get_current_user
from app.modules.dice.preset_schemas import (
    DicePresetCreate,
    DicePresetListResponse,
    DicePresetPatch,
    DicePresetResponse,
)
from app.modules.dice.preset_service import DicePresetService
from app.modules.users.models import User

router = APIRouter(prefix="/dice-presets", tags=["dice-presets"])

dice_preset_service = DicePresetService()


@router.get("", response_model=DicePresetListResponse)
async def get_dice_presets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DicePresetListResponse:
    return await dice_preset_service.list_presets(db, user=current_user)


@router.post("", response_model=DicePresetResponse, status_code=status.HTTP_201_CREATED)
async def create_dice_preset(
    payload: DicePresetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DicePresetResponse:
    return await dice_preset_service.create_preset(db, user=current_user, payload=payload)


@router.patch("/{preset_id}", response_model=DicePresetResponse)
async def patch_dice_preset(
    preset_id: int,
    payload: DicePresetPatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DicePresetResponse:
    return await dice_preset_service.update_preset(
        db,
        user=current_user,
        preset_id=preset_id,
        payload=payload,
    )


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dice_preset(
    preset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    await dice_preset_service.delete_preset(db, user=current_user, preset_id=preset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
