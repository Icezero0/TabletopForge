from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.users.models import User

if TYPE_CHECKING:
    from app.modules.library.models import LibraryResource

from app.modules.rooms.constants import (
    GameRole,
    RoomJoinAuditMode,
    RoomJoinRequestAction,
    RoomJoinRequestSource,
    RoomJoinRequestStatus,
    RoomVisibility,
)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    visibility: Mapped[RoomVisibility] = mapped_column(
        String(16),
        nullable=False,
        default=RoomVisibility.PRIVATE,
        server_default=RoomVisibility.PRIVATE.value,
        index=True,
    )
    join_audit_mode: Mapped[RoomJoinAuditMode] = mapped_column(
        String(32),
        nullable=False,
        default=RoomJoinAuditMode.MANUAL_REVIEW,
        server_default=RoomJoinAuditMode.MANUAL_REVIEW.value,
        index=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])

    members: Mapped[list["RoomMember"]] = relationship(
        "RoomMember",
        back_populates="room",
        cascade="all, delete-orphan",
    )


class RoomMember(Base):
    __tablename__ = "room_members"

    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    game_role: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default=GameRole.PL.value,
        server_default=GameRole.PL.value,
    )
    player_color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    room: Mapped["Room"] = relationship("Room", back_populates="members")
    user: Mapped["User"] = relationship("User")


class RoomJoinRequest(Base):
    __tablename__ = "room_join_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    initiator_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source: Mapped[RoomJoinRequestSource] = mapped_column(
        String(16),
        nullable=False,
        index=True,
    )
    status: Mapped[RoomJoinRequestStatus] = mapped_column(
        String(16),
        nullable=False,
        index=True,
        default=RoomJoinRequestStatus.PENDING,
    )

    room_action: Mapped[RoomJoinRequestAction] = mapped_column(
        String(16),
        nullable=False,
        default=RoomJoinRequestAction.PENDING,
    )

    target_action: Mapped[RoomJoinRequestAction] = mapped_column(
        String(16),
        nullable=False,
        default=RoomJoinRequestAction.PENDING,
    )

    room_action_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    room: Mapped["Room"] = relationship("Room")
    initiator: Mapped["User"] = relationship("User", foreign_keys=[initiator_user_id])
    target: Mapped["User"] = relationship("User", foreign_keys=[target_user_id])
    room_action_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[room_action_by_user_id],
    )


class RoomPersonalMemo(Base):
    __tablename__ = "room_personal_memos"
    __table_args__ = (
        UniqueConstraint("user_id", "room_id", name="uq_room_personal_memos_user_room"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User")
    room: Mapped["Room"] = relationship("Room")


class RoomTabletopSettings(Base):
    __tablename__ = "room_tabletop_settings"

    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    grid_cell_ft: Mapped[float] = mapped_column(Float, nullable=False, default=5.0, server_default="5")
    grid_cell_px: Mapped[int] = mapped_column(Integer, nullable=False, default=40, server_default="40")
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    room: Mapped["Room"] = relationship("Room")


class RoomMap(Base):
    __tablename__ = "room_maps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    library_resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("library_resources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    scale: Mapped[float] = mapped_column(Float, nullable=False, default=1.0, server_default="1")
    scale_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    scale_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    room: Mapped["Room"] = relationship("Room")
    library_resource: Mapped["LibraryResource"] = relationship("LibraryResource")


class RoomDrawing(Base):
    __tablename__ = "room_drawings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    geometry: Mapped[dict] = mapped_column(JSON, nullable=False)
    style: Mapped[dict] = mapped_column(JSON, nullable=False)
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_by_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    room: Mapped["Room"] = relationship("Room")
    created_by: Mapped["User"] = relationship("User")


class RoomToken(Base):
    __tablename__ = "room_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    library_resource_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("library_resources.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    linked_character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    rotation: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    panel: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    owner_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    room: Mapped["Room"] = relationship("Room")
    owner: Mapped["User"] = relationship("User")
    library_resource: Mapped[Optional["LibraryResource"]] = relationship("LibraryResource")

    @property
    def asset_id(self) -> int | None:
        if self.library_resource is not None:
            return self.library_resource.primary_asset_id
        return None


class RoomDiceRoll(Base):
    __tablename__ = "room_dice_rolls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    roller_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_token_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("room_tokens.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    formula: Mapped[str] = mapped_column(String(255), nullable=False)
    visibility: Mapped[str] = mapped_column(String(16), nullable=False, default="public", server_default="public")
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    detail: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    room: Mapped["Room"] = relationship("Room")
    roller: Mapped["User"] = relationship("User", foreign_keys=[roller_user_id])
    actor_token: Mapped[Optional["RoomToken"]] = relationship("RoomToken")


class RoomCharacter(Base):
    __tablename__ = "room_characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")
    added_by_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    room: Mapped["Room"] = relationship("Room")
    character: Mapped["Character"] = relationship("Character")
    added_by: Mapped["User"] = relationship("User", foreign_keys=[added_by_user_id])
