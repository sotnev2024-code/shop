"""Add try_on_attempts to user

Revision ID: add_try_on_attempts
Revises: move_banner_to_app
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_try_on_attempts"
down_revision: Union[str, None] = "move_banner_to_app"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("try_on_attempts", sa.Integer(), server_default="3", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "try_on_attempts")
