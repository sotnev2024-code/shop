"""add_category_parent_id

Revision ID: 249c1ab7ad4f
Revises: 
Create Date: 2026-02-21 18:04:17.714904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '249c1ab7ad4f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("categories") as batch_op:
        batch_op.add_column(
            sa.Column("parent_id", sa.Integer(), nullable=True),
        )
        batch_op.create_foreign_key(
            "fk_categories_parent_id_categories",
            "categories",
            ["parent_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_categories_parent_id",
            ["parent_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("categories") as batch_op:
        batch_op.drop_index("ix_categories_parent_id", table_name="categories")
        batch_op.drop_constraint(
            "fk_categories_parent_id_categories",
            type_="foreignkey",
        )
        batch_op.drop_column("parent_id")





