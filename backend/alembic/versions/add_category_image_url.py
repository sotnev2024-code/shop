"""Add category image_url

Revision ID: add_category_image_url
Revises: move_banner_to_app
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_category_image_url"
down_revision: Union[str, None] = "move_banner_to_app"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("image_url", sa.String(1000), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("categories", "image_url")
