"""Add daily_matches_forum_chat_id and daily_matches_forum_topic_id to app_config.

Revision ID: add_daily_matches_forum
Revises: add_order_notif_chat
Create Date: 2026-03-12

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_daily_matches_forum"
down_revision: Union[str, None] = "add_order_notif_chat"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("daily_matches_forum_chat_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "app_config",
        sa.Column("daily_matches_forum_topic_id", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_config", "daily_matches_forum_topic_id")
    op.drop_column("app_config", "daily_matches_forum_chat_id")
