"""Add delivery cost and free delivery min amount (app_config), delivery_fee (orders)

Revision ID: add_delivery_cost
Revises: add_bonus_system
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_delivery_cost"
down_revision: Union[str, None] = "add_bonus_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("delivery_cost", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("free_delivery_min_amount", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "orders",
        sa.Column("delivery_fee", sa.Numeric(10, 2), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("orders", "delivery_fee")
    op.drop_column("app_config", "free_delivery_min_amount")
    op.drop_column("app_config", "delivery_cost")
