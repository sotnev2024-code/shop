"""Add bonus system: users.bonus_balance, orders.bonus_used, app_config bonus fields, bonus_transactions

Revision ID: add_bonus_system
Revises: add_cat_img_size
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_bonus_system"
down_revision: Union[str, tuple[str, ...], None] = ("add_cat_img_size", "add_category_image_url")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("bonus_balance", sa.Numeric(10, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "orders",
        sa.Column("bonus_used", sa.Numeric(10, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("bonus_enabled", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("bonus_welcome_enabled", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("bonus_welcome_amount", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("bonus_purchase_enabled", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("bonus_purchase_percent", sa.Float(), server_default="0", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("bonus_spend_enabled", sa.Boolean(), server_default="0", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("bonus_spend_limit_type", sa.String(20), server_default="percent", nullable=False),
    )
    op.add_column(
        "app_config",
        sa.Column("bonus_spend_limit_value", sa.Float(), server_default="0", nullable=False),
    )
    op.create_table(
        "bonus_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bonus_transactions_user_id"), "bonus_transactions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bonus_transactions_user_id"), table_name="bonus_transactions")
    op.drop_table("bonus_transactions")
    op.drop_column("app_config", "bonus_spend_limit_value")
    op.drop_column("app_config", "bonus_spend_limit_type")
    op.drop_column("app_config", "bonus_spend_enabled")
    op.drop_column("app_config", "bonus_purchase_percent")
    op.drop_column("app_config", "bonus_purchase_enabled")
    op.drop_column("app_config", "bonus_welcome_amount")
    op.drop_column("app_config", "bonus_welcome_enabled")
    op.drop_column("app_config", "bonus_enabled")
    op.drop_column("orders", "bonus_used")
    op.drop_column("users", "bonus_balance")
