"""add_user_name

Revision ID: 0003_add_user_name
Revises: 0002_add_chat_and_message
Create Date: 2026-06-06 05:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "0003_add_user_name"
down_revision = "0002_add_chat_and_message"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add `name` column only if it does not already exist (idempotent migration)
    conn = op.get_bind()
    inspector = inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("users")] if inspector.get_columns("users") else []
    if "name" not in cols:
        op.add_column('users', sa.Column('name', sa.String(length=150), nullable=True, server_default=''))


def downgrade() -> None:
    op.drop_column('users', 'name')
