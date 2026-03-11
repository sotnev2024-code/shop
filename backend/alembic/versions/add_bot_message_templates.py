"""Add bot_message_templates to app_config.

Revision ID: add_bot_templates
Revises: add_posts_table
Create Date: 2026-03-12

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_bot_templates"
down_revision: Union[str, None] = "add_posts_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_config",
        sa.Column("bot_message_templates", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("app_config", "bot_message_templates")
