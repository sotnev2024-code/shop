"""Add football_betting_enabled toggle to app_config.

Revision ID: add_football_betting_toggle
Revises: add_try_on_bonus_flag
Create Date: 2026-03-23

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_football_betting_toggle"
down_revision: Union[str, None] = "add_try_on_bonus_flag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("football_betting_enabled", sa.Boolean(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("app_config", "football_betting_enabled")
