"""product_categories many-to-many: product can have multiple categories

Revision ID: product_categories_m2m
Revises: add_delivery_cost
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "product_categories_m2m"
down_revision: Union[str, None] = "add_delivery_cost"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("product_id", "category_id"),
    )
    op.create_index(
        op.f("ix_product_categories_category_id"),
        "product_categories",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_product_categories_product_id"),
        "product_categories",
        ["product_id"],
        unique=False,
    )

    # Migrate existing product.category_id into product_categories
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "INSERT INTO product_categories (product_id, category_id) "
            "SELECT id, category_id FROM products WHERE category_id IS NOT NULL"
        )
    )

    # Drop category_id from products (batch_alter handles SQLite table recreate)
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_column("category_id")


def downgrade() -> None:
    # Re-add category_id to products
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("category_id", sa.Integer(), nullable=True))

    # Restore first category per product from product_categories
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE products SET category_id = ("
            "SELECT category_id FROM product_categories "
            "WHERE product_categories.product_id = products.id LIMIT 1"
            ")"
        )
    )

    op.drop_index("ix_product_categories_product_id", "product_categories")
    op.drop_index("ix_product_categories_category_id", "product_categories")
    op.drop_table("product_categories")
