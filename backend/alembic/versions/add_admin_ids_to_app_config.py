"""Add admin_ids to app_config (comma-separated telegram_id, overrides .env)

Revision ID: add_admin_ids
Revises: add_min_order_amount
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_admin_ids"
down_revision: Union[str, None] = "add_min_order_amount"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("admin_ids", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_config", "admin_ids")
