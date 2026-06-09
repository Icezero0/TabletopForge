from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, ForbiddenError
from app.modules.dice.engine import DiceFormulaError, evaluate_formula
from app.modules.character.repository import CharacterRepository
from app.modules.rooms.constants import GamePermission, GameRole, RoomPermission
from app.modules.rooms.dice.repository import RoomDiceRepository
from app.modules.rooms.dice.schemas import DiceRollCreate, DiceRollListResponse, DiceRollResponse
from app.modules.rooms.game_permissions import require_game_permission
from app.modules.rooms.membership.service import RoomMembershipService
from app.modules.rooms.permissions import require_room_permission
from app.modules.rooms.room.service import RoomService
from app.modules.rooms.models import RoomDiceRoll, RoomToken
from app.modules.users.models import User


class RoomDiceService:
    def __init__(self) -> None:
        self.repo = RoomDiceRepository()
        self.room_service = RoomService()
        self.membership_service = RoomMembershipService()
        self.character_repo = CharacterRepository()

    async def create_roll(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        payload: DiceRollCreate,
    ) -> tuple[DiceRollResponse, DiceRollResponse, list[int]]:
        game_role = await self._require_room_permission(
            db,
            room_id=room_id,
            user_id=user.id,
            permission=RoomPermission.SEND_MESSAGE,
        )

        actor_token_id = payload.actor_token_id
        actor_display_name = user.username or user.email
        if payload.actor_type == "token":
            if actor_token_id is None:
                raise BadRequestError(
                    "actor_token_id is required for token dice actor",
                    reason=ErrorReason.INVALID_PAYLOAD,
                )
            token = await self.repo.find_token(db, room_id=room_id, token_id=actor_token_id)
            if token is None:
                raise BadRequestError(
                    "Token not found in room",
                    reason=ErrorReason.INVALID_PAYLOAD,
                    details={"token_id": actor_token_id},
                )
            await self._require_token_actor_access(
                db,
                game_role=game_role,
                user=user,
                token=token,
            )
            actor_display_name = token.name
        else:
            actor_token_id = None

        try:
            evaluated = evaluate_formula(payload.formula)
        except DiceFormulaError as exc:
            raise BadRequestError(str(exc), reason=ErrorReason.INVALID_PAYLOAD) from exc
        roll = await self.repo.create_roll(
            db,
            room_id=room_id,
            roller_user_id=user.id,
            actor_type=payload.actor_type,
            actor_token_id=actor_token_id,
            actor_display_name=actor_display_name,
            label=payload.label.strip(),
            formula=evaluated.formula,
            visibility=payload.visibility,
            total=evaluated.total,
            detail=evaluated.detail,
        )
        roll_id = roll.id
        await db.commit()
        stored = await self.repo.find_roll_by_id(db, roll_id)
        if stored is None:
            raise BadRequestError("Dice roll was not saved", reason=ErrorReason.APP_ERROR)

        full = self._build_response(stored, hidden=False)
        public = self._build_response(stored, hidden=payload.visibility == "blind")
        gm_user_ids = await self.repo.get_gm_user_ids(db, room_id=room_id) if payload.visibility == "blind" else []
        return public, full, gm_user_ids

    async def get_rolls(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user: User,
        before_id: int | None = None,
        limit: int = 30,
    ) -> DiceRollListResponse:
        game_role = await self._require_room_permission(
            db,
            room_id=room_id,
            user_id=user.id,
            permission=RoomPermission.VIEW_MESSAGES,
        )
        rolls = await self.repo.get_rolls_by_room_id(
            db,
            room_id=room_id,
            before_id=before_id,
            limit=limit,
            include_blind=game_role == GameRole.GM,
        )
        next_before_id = rolls[-1].id if len(rolls) == limit else None
        return DiceRollListResponse(
            items=[
                self._build_response(roll, hidden=False)
                for roll in reversed(rolls)
            ],
            next_before_id=next_before_id,
        )

    async def _require_token_actor_access(
        self,
        db: AsyncSession,
        *,
        game_role: GameRole,
        user: User,
        token: RoomToken,
    ) -> None:
        if game_role == GameRole.GM:
            require_game_permission(game_role, GamePermission.MANAGE_ANY_TOKEN)
            return
        if game_role == GameRole.PL:
            require_game_permission(game_role, GamePermission.MOVE_OWN_CHARACTER_TOKEN)
            if token.linked_character_id is not None:
                character = await self.character_repo.get_by_id(
                    db,
                    character_id=token.linked_character_id,
                )
                if character is not None and character.owner_id == user.id:
                    return
            elif token.owner_user_id == user.id:
                return
        raise ForbiddenError(
            "You do not have permission to use this token as dice actor",
            reason=ErrorReason.ROOM_PERMISSION_DENIED,
            details={"token_id": token.id, "game_role": game_role},
        )

    async def _require_room_permission(
        self,
        db: AsyncSession,
        *,
        room_id: int,
        user_id: int,
        permission: RoomPermission,
    ) -> GameRole:
        await self.room_service.get_room_by_id(db, room_id)
        role = await self.membership_service.find_room_role(
            db,
            room_id=room_id,
            user_id=user_id,
        )
        if role is None:
            raise ForbiddenError(
                "You do not have permission to perform this action",
                reason=ErrorReason.ROOM_PERMISSION_DENIED,
                details={"room_id": room_id, "permission": permission.value},
            )
        require_room_permission(role, permission)

        game_role = await self.membership_service.find_game_role(
            db,
            room_id=room_id,
            user_id=user_id,
        )
        return game_role or GameRole.OB

    def _build_response(self, roll: RoomDiceRoll, *, hidden: bool) -> DiceRollResponse:
        return DiceRollResponse(
            id=roll.id,
            room_id=roll.room_id,
            roller_user_id=roll.roller_user_id,
            actor_type=roll.actor_type,
            actor_token_id=roll.actor_token_id,
            actor_display_name=roll.actor_display_name,
            label=roll.label,
            formula=roll.formula,
            visibility=roll.visibility,
            total=None if hidden else roll.total,
            detail=None if hidden else roll.detail,
            hidden=hidden,
            created_at=roll.created_at,
        )
