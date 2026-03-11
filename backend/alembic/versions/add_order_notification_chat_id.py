"""Add order_notification_chat_id to app_config.

Revision ID: add_order_notif_chat
Revises: add_bot_templates
Create Date: 2026-03-12

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_order_notif_chat"
down_revision: Union[str, None] = "add_bot_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("order_notification_chat_id", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_config", "order_notification_chat_id")
