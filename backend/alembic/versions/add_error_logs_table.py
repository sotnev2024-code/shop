"""Add error_logs table for centralized error logging.

Revision ID: add_error_logs
Revises: add_competition_bets
Create Date: 2026-03-11

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_error_logs"
down_revision: Union[str, None] = "add_competition_bets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "error_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("level", sa.String(length=20), server_default="ERROR", nullable=False),
        sa.Column("message", sa.String(length=500), server_default="", nullable=False),
        sa.Column("path", sa.String(length=255), nullable=True),
        sa.Column("method", sa.String(length=10), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("client_ip", sa.String(length=50), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("request_body", sa.Text(), nullable=True),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("error_logs")

