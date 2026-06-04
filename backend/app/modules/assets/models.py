from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.assets.constants import AssetType


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        Index("idx_assets_owner_type_created_at", "owner_id", "asset_type", "created_at"),
        Index("idx_assets_feedback_id", "feedback_id"),
        Index("idx_assets_type_hash_size_content_type", "asset_type", "content_hash", "size_bytes", "content_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)
    owner_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    feedback_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("feedbacks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ref_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    owner = relationship("User", foreign_keys=[owner_id])
    feedback = relationship("Feedback", back_populates="images")

    @property
    def is_avatar(self) -> bool:
        return self.asset_type == AssetType.AVATAR

    @property
    def is_feedback_image(self) -> bool:
        return self.asset_type == AssetType.FEEDBACK_IMAGE

    @property
    def is_user_library_asset(self) -> bool:
        return self.asset_type in {AssetType.IMAGE, AssetType.AUDIO}
