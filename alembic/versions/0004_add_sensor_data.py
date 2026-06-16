"""add_sensor_data

Revision ID: 0004_add_sensor_data
Revises: 0003_add_user_name
Create Date: 2026-06-15 03:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004_add_sensor_data"
down_revision = "0003_add_user_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Ensure pgcrypto for gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.create_table(
        "sensor_data",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("air_humidity", sa.Float(), nullable=False),
        sa.Column("soil_moisture", sa.Float(), nullable=False),
        sa.Column("ph", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("update_at", sa.DateTime(timezone=False), server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.DateTime(timezone=False), nullable=True),
    )

    op.create_index("ix_sensor_data_device_id", "sensor_data", ["device_id"])
    op.create_index("ix_sensor_data_deleted_at", "sensor_data", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_sensor_data_device_id", table_name="sensor_data")
    op.drop_index("ix_sensor_data_deleted_at", table_name="sensor_data")
    op.drop_table("sensor_data")
