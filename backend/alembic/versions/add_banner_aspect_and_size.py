"""add banner aspect_shape and size

Revision ID: add_banner_aspect_size
Revises: 249c1ab7ad4f
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_banner_aspect_size"
down_revision: Union[str, None] = "249c1ab7ad4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("banners", sa.Column("aspect_shape", sa.String(20), server_default="rectangle", nullable=False))
    op.add_column("banners", sa.Column("size", sa.String(20), server_default="medium", nullable=False))


def downgrade() -> None:
    op.drop_column("banners", "size")
    op.drop_column("banners", "aspect_shape")
