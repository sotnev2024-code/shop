"""Add competition_points_balance to users (for football leaderboard)

Revision ID: add_competition_pts
Revises: add_admin_ids
Create Date: 2026-03-09

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_competition_pts"
down_revision: Union[str, None] = "add_admin_ids"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("competition_points_balance", sa.Numeric(12, 2), server_default="10000", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "competition_points_balance")
