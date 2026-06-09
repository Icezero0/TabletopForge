from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_realtime_publisher
from app.core.database import get_db
from app.modules.auth.deps import get_current_user
from app.modules.rooms.dice.schemas import DiceRollCreate, DiceRollListResponse, DiceRollResponse
from app.modules.rooms.dice.service import RoomDiceService
from app.modules.users.models import User
from app.realtime.publisher import RealtimePublisher

router = APIRouter(prefix="/rooms/{room_id}/dice-rolls", tags=["dice"])

dice_service = RoomDiceService()


@router.post("", response_model=DiceRollResponse, status_code=status.HTTP_201_CREATED)
async def create_dice_roll(
    room_id: int,
    payload: DiceRollCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    publisher: RealtimePublisher = Depends(get_realtime_publisher),
) -> DiceRollResponse:
    public_roll, full_roll, gm_user_ids = await dice_service.create_roll(
        db,
        room_id=room_id,
        user=current_user,
        payload=payload,
    )
    if payload.visibility == "blind":
        for user_id in gm_user_ids:
            await publisher.publish_dice_roll_to_user(
                user_id=user_id,
                roll=full_roll.model_dump(mode="json"),
            )
    else:
        await publisher.publish_dice_roll(
            room_id=room_id,
            roll=public_roll.model_dump(mode="json"),
        )
    return full_roll if current_user.id in gm_user_ids or payload.visibility == "public" else public_roll


@router.get("", response_model=DiceRollListResponse)
async def get_dice_rolls(
    room_id: int,
    before_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DiceRollListResponse:
    return await dice_service.get_rolls(
        db,
        room_id=room_id,
        user=current_user,
        before_id=before_id,
        limit=limit,
    )
