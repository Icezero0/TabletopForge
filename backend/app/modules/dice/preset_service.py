from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_reasons import ErrorReason
from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.dice.preset_repository import DicePresetRepository
from app.modules.dice.preset_schemas import DicePresetCreate, DicePresetListResponse, DicePresetPatch, DicePresetResponse
from app.modules.rooms.models import DicePreset
from app.modules.users.models import User


class DicePresetService:
    def __init__(self) -> None:
        self.repo = DicePresetRepository()

    async def list_presets(self, db: AsyncSession, *, user: User) -> DicePresetListResponse:
        presets = await self.repo.list_by_owner(db, owner_id=user.id)
        return DicePresetListResponse(items=[DicePresetResponse.model_validate(item) for item in presets])

    async def create_preset(self, db: AsyncSession, *, user: User, payload: DicePresetCreate) -> DicePresetResponse:
        await self._validate_parent(db, owner_id=user.id, parent_id=payload.parent_id)
        preset = await self.repo.create(
            db,
            owner_id=user.id,
            parent_id=payload.parent_id,
            kind=payload.kind,
            name=payload.name.strip(),
            formula=payload.formula.strip() if payload.kind == "preset" else "",
            label=payload.label.strip() if payload.kind == "preset" else "",
            visibility=payload.visibility if payload.kind == "preset" else "public",
            sort_order=payload.sort_order,
        )
        await db.commit()
        await db.refresh(preset)
        return DicePresetResponse.model_validate(preset)

    async def update_preset(
        self,
        db: AsyncSession,
        *,
        user: User,
        preset_id: int,
        payload: DicePresetPatch,
    ) -> DicePresetResponse:
        preset = await self._get_owned(db, owner_id=user.id, preset_id=preset_id)
        fields = payload.model_fields_set

        if "parent_id" in fields:
            await self._validate_parent(
                db,
                owner_id=user.id,
                parent_id=payload.parent_id,
                moving_id=preset.id,
            )
            preset.parent_id = payload.parent_id
        if payload.kind is not None:
            preset.kind = payload.kind
        if payload.name is not None:
            preset.name = payload.name.strip()
        if payload.formula is not None:
            preset.formula = payload.formula.strip()
        if payload.label is not None:
            preset.label = payload.label.strip()
        if payload.visibility is not None:
            preset.visibility = payload.visibility
        if payload.sort_order is not None:
            preset.sort_order = payload.sort_order

        if preset.kind == "folder":
            preset.formula = ""
            preset.label = ""
            preset.visibility = "public"
        elif not preset.formula.strip():
            raise BadRequestError("Preset formula is required", reason=ErrorReason.INVALID_PAYLOAD)

        await db.commit()
        await db.refresh(preset)
        return DicePresetResponse.model_validate(preset)

    async def delete_preset(self, db: AsyncSession, *, user: User, preset_id: int) -> None:
        preset = await self._get_owned(db, owner_id=user.id, preset_id=preset_id)
        presets = await self.repo.list_by_owner(db, owner_id=user.id)
        child_ids_by_parent: dict[int, list[int]] = {}
        for item in presets:
            if item.parent_id is None:
                continue
            child_ids_by_parent.setdefault(item.parent_id, []).append(item.id)
        deleting_ids: set[int] = set()

        def collect_descendants(item_id: int) -> None:
            deleting_ids.add(item_id)
            for child_id in child_ids_by_parent.get(item_id, []):
                collect_descendants(child_id)

        collect_descendants(preset.id)
        parent_by_id = {item.id: item.parent_id for item in presets}

        def depth(item_id: int) -> int:
            value = 0
            cursor = parent_by_id.get(item_id)
            while cursor is not None:
                value += 1
                cursor = parent_by_id.get(cursor)
            return value

        for item in sorted(presets, key=lambda entry: depth(entry.id), reverse=True):
            if item.id in deleting_ids:
                await self.repo.delete(db, item)
        await db.commit()

    async def _get_owned(self, db: AsyncSession, *, owner_id: int, preset_id: int) -> DicePreset:
        preset = await self.repo.find_by_id(db, owner_id=owner_id, preset_id=preset_id)
        if preset is None:
            raise NotFoundError("Dice preset not found", reason=ErrorReason.INVALID_PAYLOAD)
        return preset

    async def _validate_parent(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        parent_id: int | None,
        moving_id: int | None = None,
    ) -> None:
        if parent_id is None:
            return
        if moving_id is not None and parent_id == moving_id:
            raise BadRequestError("A preset cannot be moved into itself", reason=ErrorReason.INVALID_PAYLOAD)
        parent = await self.repo.find_by_id(db, owner_id=owner_id, preset_id=parent_id)
        if parent is None or parent.kind != "folder":
            raise BadRequestError("Parent folder not found", reason=ErrorReason.INVALID_PAYLOAD)
        if moving_id is None:
            return

        presets = await self.repo.list_by_owner(db, owner_id=owner_id)
        parent_by_id = {item.id: item.parent_id for item in presets}
        cursor = parent_id
        while cursor is not None:
            if cursor == moving_id:
                raise BadRequestError("A folder cannot be moved into its descendant", reason=ErrorReason.INVALID_PAYLOAD)
            cursor = parent_by_id.get(cursor)
