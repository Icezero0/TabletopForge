from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, func
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
    token_image_asset_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    system: Mapped[str] = mapped_column(
        String(50), nullable=False, default="dnd5e", server_default="dnd5e"
    )

    identity: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    flavor: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    spells: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resources: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
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
    token_image_asset = relationship("Asset", foreign_keys=[token_image_asset_id])
    state = relationship(
        "CharacterState",
        back_populates="character",
        uselist=False,
        cascade="all, delete-orphan",
    )
    token_configs = relationship(
        "CharacterTokenConfig",
        back_populates="character",
        cascade="all, delete-orphan",
        order_by="(CharacterTokenConfig.is_primary.desc(), CharacterTokenConfig.sort_order)",
    )


class CharacterTokenConfig(Base):
    __tablename__ = "character_token_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="", server_default="")
    asset_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    library_resource_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("library_resources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    panel_initial: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, server_default="{}"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    character = relationship("Character", back_populates="token_configs")
    asset = relationship("Asset", foreign_keys=[asset_id])


class CharacterState(Base):
    __tablename__ = "character_states"

    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    current_hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_hp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temp_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    armor_class: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    damage_taken: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    character = relationship("Character", back_populates="state")
