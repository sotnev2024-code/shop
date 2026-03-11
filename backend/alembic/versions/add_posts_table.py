"""Add posts table for channel posts.

Revision ID: add_posts_table
Revises: add_channel_id
Create Date: 2026-03-12

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_posts_table"
down_revision: Union[str, None] = "add_channel_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("photo_url", sa.String(1000), nullable=True),
        sa.Column("photo_file_id", sa.String(255), nullable=True),
        sa.Column("button_text", sa.String(255), nullable=True),
        sa.Column("button_url", sa.String(1000), nullable=True),
        sa.Column("button_color", sa.String(50), nullable=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("channel_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("posts")
