"""Add autopost settings to app_config.

Revision ID: add_autopost_settings
Revises: add_daily_matches_forum
Create Date: 2026-03

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_autopost_settings"
down_revision: Union[str, None] = "add_daily_matches_forum"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("autopost_enabled", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "app_config",
        sa.Column("autopost_times", sa.String(500), nullable=True),
    )
    op.add_column(
        "app_config",
        sa.Column("autopost_posts_per_day", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "app_config",
        sa.Column("autopost_template", sa.Text(), nullable=True),
    )
    op.add_column(
        "app_config",
        sa.Column("autopost_button_text", sa.String(255), nullable=True),
    )
    op.add_column(
        "app_config",
        sa.Column("autopost_button_color", sa.String(50), nullable=True),
    )
    op.add_column(
        "app_config",
        sa.Column("autopost_last_product_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "app_config",
        sa.Column("autopost_hide_price", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("app_config", "autopost_hide_price")
    op.drop_column("app_config", "autopost_last_product_index")
    op.drop_column("app_config", "autopost_button_color")
    op.drop_column("app_config", "autopost_button_text")
    op.drop_column("app_config", "autopost_template")
    op.drop_column("app_config", "autopost_posts_per_day")
    op.drop_column("app_config", "autopost_times")
    op.drop_column("app_config", "autopost_enabled")
