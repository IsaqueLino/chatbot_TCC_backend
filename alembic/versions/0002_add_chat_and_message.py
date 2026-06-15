"""add_chat_and_message

Revision ID: 0002_add_chat_and_message
Revises: 0001_initial
Create Date: 2026-06-06 05:20:00.000000

"""
from alembic import op
from sqlmodel import SQLModel

import app.models  # ensure models are imported so SQLModel.metadata is populated

# revision identifiers, used by Alembic.
revision = "0002_add_chat_and_message"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Create all tables defined in SQLModel metadata (new models will be created)
    SQLModel.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    SQLModel.metadata.drop_all(bind=bind)
