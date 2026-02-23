"""Add promo first_order_only

Revision ID: add_promo_first_order
Revises: add_delivery_cost
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_promo_first_order"
down_revision: Union[str, None] = "add_delivery_cost"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "promo_codes",
        sa.Column("first_order_only", sa.Boolean(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("promo_codes", "first_order_only")
