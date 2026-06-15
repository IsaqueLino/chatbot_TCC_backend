"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-06-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Ensure pgcrypto for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # Users table with UUID PK
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False, server_default=""),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("level", sa.String(length=32), nullable=False, server_default=sa.text("'USER'")),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("update_at", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=False), nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # Note: session persistence removed; sessions are stateless JWTs handled by the auth system.

    # Chats table
    op.create_table(
        "chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=sa.text("'New Chat'")),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("update_at", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=False), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_chats_user_id"),
    )

    # Messages table
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("update_at", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=False), nullable=True),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], name="fk_messages_chat_id"),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("chats")
    op.drop_table("users")
