from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LibraryResource(Base):
    __tablename__ = "library_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    primary_asset_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    meta: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    map_grid_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_grid_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_grid_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_grid_cell_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    map_grid_calibration: Mapped[list | None] = mapped_column(JSON, nullable=True)

    usage_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )

    owner = relationship("User", foreign_keys=[owner_id])
    primary_asset = relationship("Asset", foreign_keys=[primary_asset_id])
