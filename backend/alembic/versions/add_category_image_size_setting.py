"""Add category_image_size to app_config

Revision ID: add_cat_img_size
Revises: move_banner_to_app
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_cat_img_size"
down_revision: Union[str, None] = "move_banner_to_app"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("category_image_size", sa.String(20), server_default="medium", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("app_config", "category_image_size")
