"""Add try_on_bonus_received and update try_on_attempts default

Revision ID: add_try_on_bonus_flag
Revises: add_try_on_attempts
Create Date: 2026-03-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_try_on_bonus_flag"
down_revision: Union[str, None] = "add_try_on_attempts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Set default to 0 for new users
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("try_on_bonus_received", sa.Boolean(), server_default="0", nullable=False),
        )
        # We don't change existing users' attempts here, but for new ones it will be 0 via SQLAlchemy default.


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("try_on_bonus_received")
