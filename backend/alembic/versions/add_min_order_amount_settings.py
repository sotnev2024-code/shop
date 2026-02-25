"""Add min order amount for pickup and delivery (app_config)

Revision ID: add_min_order_amount
Revises: add_promo_first_order
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_min_order_amount"
down_revision: Union[str, None] = "add_promo_first_order"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("min_order_amount_pickup", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("min_order_amount_delivery", sa.Float(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("app_config", "min_order_amount_delivery")
    op.drop_column("app_config", "min_order_amount_pickup")
