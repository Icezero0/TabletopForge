"""initial schema

Revision ID: 20260604_0001
Revises:
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260604_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("avatar_asset_id", sa.Integer(), nullable=True),
        sa.Column("site_role", sa.String(length=16), server_default="user", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("visibility", sa.String(length=16), server_default="private", nullable=False),
        sa.Column("join_audit_mode", sa.String(length=32), server_default="manual_review", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_id"), "rooms", ["id"], unique=False)
    op.create_index(op.f("ix_rooms_join_audit_mode"), "rooms", ["join_audit_mode"], unique=False)
    op.create_index(op.f("ix_rooms_owner_id"), "rooms", ["owner_id"], unique=False)
    op.create_index(op.f("ix_rooms_visibility"), "rooms", ["visibility"], unique=False)

    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("creator_id", sa.Integer(), nullable=False),
        sa.Column("handled_by_id", sa.Integer(), nullable=True),
        sa.Column("feedback_type", sa.String(length=32), server_default="bug", nullable=False),
        sa.Column("page", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="open", nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["creator_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["handled_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_feedbacks_creator_id_created_at", "feedbacks", ["creator_id", "created_at"], unique=False)
    op.create_index("idx_feedbacks_status_created_at", "feedbacks", ["status", "created_at"], unique=False)
    op.create_index(op.f("ix_feedbacks_creator_id"), "feedbacks", ["creator_id"], unique=False)
    op.create_index(op.f("ix_feedbacks_handled_by_id"), "feedbacks", ["handled_by_id"], unique=False)

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("feedback_id", sa.Integer(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["feedback_id"], ["feedbacks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_assets_feedback_id", "assets", ["feedback_id"], unique=False)
    op.create_index("idx_assets_owner_type_created_at", "assets", ["owner_id", "asset_type", "created_at"], unique=False)
    op.create_index(op.f("ix_assets_feedback_id"), "assets", ["feedback_id"], unique=False)
    op.create_index(op.f("ix_assets_owner_id"), "assets", ["owner_id"], unique=False)

    op.create_table(
        "room_members",
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("room_id", "user_id"),
    )

    op.create_table(
        "room_join_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("initiator_user_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("room_action", sa.String(length=16), nullable=False),
        sa.Column("target_action", sa.String(length=16), nullable=False),
        sa.Column("room_action_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["initiator_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_action_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_join_requests_id"), "room_join_requests", ["id"], unique=False)
    op.create_index(op.f("ix_room_join_requests_initiator_user_id"), "room_join_requests", ["initiator_user_id"], unique=False)
    op.create_index(op.f("ix_room_join_requests_room_action_by_user_id"), "room_join_requests", ["room_action_by_user_id"], unique=False)
    op.create_index(op.f("ix_room_join_requests_room_id"), "room_join_requests", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_join_requests_source"), "room_join_requests", ["source"], unique=False)
    op.create_index(op.f("ix_room_join_requests_status"), "room_join_requests", ["status"], unique=False)
    op.create_index(op.f("ix_room_join_requests_target_user_id"), "room_join_requests", ["target_user_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("notification_type", sa.String(length=32), nullable=False),
        sa.Column("related_type", sa.String(length=64), nullable=True),
        sa.Column("related_id", sa.Integer(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_actor_user_id"), "notifications", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_notifications_created_at"), "notifications", ["created_at"], unique=False)
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"], unique=False)
    op.create_index(op.f("ix_notifications_notification_type"), "notifications", ["notification_type"], unique=False)
    op.create_index(op.f("ix_notifications_recipient_user_id"), "notifications", ["recipient_user_id"], unique=False)
    op.create_index(op.f("ix_notifications_related_id"), "notifications", ["related_id"], unique=False)
    op.create_index(op.f("ix_notifications_related_type"), "notifications", ["related_type"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sender_user_id", sa.Integer(), nullable=True),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_created_at"), "messages", ["created_at"], unique=False)
    op.create_index(op.f("ix_messages_id"), "messages", ["id"], unique=False)
    op.create_index(op.f("ix_messages_room_id"), "messages", ["room_id"], unique=False)
    op.create_index(op.f("ix_messages_sender_user_id"), "messages", ["sender_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_messages_sender_user_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_room_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_created_at"), table_name="messages")
    op.drop_table("messages")

    op.drop_index(op.f("ix_notifications_related_type"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_related_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_recipient_user_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_notification_type"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_created_at"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_actor_user_id"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(op.f("ix_room_join_requests_target_user_id"), table_name="room_join_requests")
    op.drop_index(op.f("ix_room_join_requests_status"), table_name="room_join_requests")
    op.drop_index(op.f("ix_room_join_requests_source"), table_name="room_join_requests")
    op.drop_index(op.f("ix_room_join_requests_room_id"), table_name="room_join_requests")
    op.drop_index(op.f("ix_room_join_requests_room_action_by_user_id"), table_name="room_join_requests")
    op.drop_index(op.f("ix_room_join_requests_initiator_user_id"), table_name="room_join_requests")
    op.drop_index(op.f("ix_room_join_requests_id"), table_name="room_join_requests")
    op.drop_table("room_join_requests")

    op.drop_table("room_members")

    op.drop_index(op.f("ix_assets_owner_id"), table_name="assets")
    op.drop_index(op.f("ix_assets_feedback_id"), table_name="assets")
    op.drop_index("idx_assets_owner_type_created_at", table_name="assets")
    op.drop_index("idx_assets_feedback_id", table_name="assets")
    op.drop_table("assets")

    op.drop_index(op.f("ix_feedbacks_handled_by_id"), table_name="feedbacks")
    op.drop_index(op.f("ix_feedbacks_creator_id"), table_name="feedbacks")
    op.drop_index("idx_feedbacks_status_created_at", table_name="feedbacks")
    op.drop_index("idx_feedbacks_creator_id_created_at", table_name="feedbacks")
    op.drop_table("feedbacks")

    op.drop_index(op.f("ix_rooms_visibility"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_owner_id"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_join_audit_mode"), table_name="rooms")
    op.drop_index(op.f("ix_rooms_id"), table_name="rooms")
    op.drop_table("rooms")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
