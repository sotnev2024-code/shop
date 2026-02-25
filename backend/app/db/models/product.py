from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Many-to-many: product can belong to several categories (including subcategories)
product_category = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    old_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    categories: Mapped[List["Category"]] = relationship(
        "Category",
        secondary=product_category,
        back_populates="products",
    )
    cart_items: Mapped[List["CartItem"]] = relationship(back_populates="product")
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="product")
    media: Mapped[List["ProductMedia"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductMedia.sort_order",
    )
    variants: Mapped[List["ProductVariant"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )

