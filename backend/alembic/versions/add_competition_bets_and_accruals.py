"""Add competition_bets and competition_accruals tables

Revision ID: add_competition_bets
Revises: add_competition_pts
Create Date: 2026-03-09

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_competition_bets"
down_revision: Union[str, None] = "add_competition_pts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "competition_bets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("fixture_id", sa.BigInteger(), nullable=False),
        sa.Column("match_label", sa.String(255), server_default="", nullable=False),
        sa.Column("outcome", sa.String(4), server_default="", nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("odds", sa.Numeric(8, 4), server_default="0", nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("payout", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_competition_bets_user_id"), "competition_bets", ["user_id"], unique=False)
    op.create_index(op.f("ix_competition_bets_fixture_id"), "competition_bets", ["fixture_id"], unique=False)

    op.create_table(
        "competition_accruals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("kind", sa.String(50), server_default="", nullable=False),
        sa.Column("description", sa.String(500), server_default="", nullable=False),
        sa.Column("bet_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_competition_accruals_user_id"), "competition_accruals", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_competition_accruals_user_id"), table_name="competition_accruals")
    op.drop_table("competition_accruals")
    op.drop_index(op.f("ix_competition_bets_fixture_id"), table_name="competition_bets")
    op.drop_index(op.f("ix_competition_bets_user_id"), table_name="competition_bets")
    op.drop_table("competition_bets")
