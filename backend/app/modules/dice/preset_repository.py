from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rooms.models import DicePreset


class DicePresetRepository:
    async def list_by_owner(self, db: AsyncSession, *, owner_id: int) -> list[DicePreset]:
        result = await db.execute(
            select(DicePreset)
            .where(DicePreset.owner_id == owner_id)
            .order_by(DicePreset.parent_id.is_not(None), DicePreset.parent_id, DicePreset.sort_order, DicePreset.id)
        )
        return list(result.scalars().all())

    async def find_by_id(self, db: AsyncSession, *, owner_id: int, preset_id: int) -> DicePreset | None:
        result = await db.execute(
            select(DicePreset).where(DicePreset.id == preset_id, DicePreset.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        parent_id: int | None,
        kind: str,
        name: str,
        formula: str,
        label: str,
        visibility: str,
        sort_order: int,
    ) -> DicePreset:
        preset = DicePreset(
            owner_id=owner_id,
            parent_id=parent_id,
            kind=kind,
            name=name,
            formula=formula,
            label=label,
            visibility=visibility,
            sort_order=sort_order,
        )
        db.add(preset)
        await db.flush()
        await db.refresh(preset)
        return preset

    async def delete(self, db: AsyncSession, preset: DicePreset) -> None:
        await db.delete(preset)
