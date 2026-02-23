"""Move banner aspect_shape and size to app_config (global settings)

Revision ID: move_banner_to_app
Revises: add_banner_aspect_size
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "move_banner_to_app"
down_revision: Union[str, None] = "add_banner_aspect_size"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("banner_aspect_shape", sa.String(20), server_default="rectangle", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("banner_size", sa.String(20), server_default="medium", nullable=False),
    )
    with op.batch_alter_table("banners") as batch_op:
        batch_op.drop_column("size")
        batch_op.drop_column("aspect_shape")


def downgrade() -> None:
    op.add_column("banners", sa.Column("aspect_shape", sa.String(20), server_default="rectangle", nullable=False))
    op.add_column("banners", sa.Column("size", sa.String(20), server_default="medium", nullable=False))
    op.drop_column("app_config", "banner_size")
    op.drop_column("app_config", "banner_aspect_shape")
