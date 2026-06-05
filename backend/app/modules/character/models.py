from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    player_name: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", server_default=""
    )
    portrait_asset_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    system: Mapped[str] = mapped_column(
        String(50), nullable=False, default="dnd5e", server_default="dnd5e"
    )

    # JSONB blocks — each covers a distinct concern of the character sheet
    identity: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    flavor: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    # None = non-caster; {} = caster with no spells configured yet
    spells: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    equipment: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    extras: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    owner = relationship("User", foreign_keys=[owner_id])
    portrait_asset = relationship("Asset", foreign_keys=[portrait_asset_id])
