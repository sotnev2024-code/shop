from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "product_id", "variant_key",
            name="uq_cart_user_product_variant",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    modification_type_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("modification_types.id", ondelete="CASCADE"), nullable=True, index=True
    )
    modification_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    variant_key: Mapped[str] = mapped_column(String(320), default="")

    user: Mapped["User"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")
    modification_type: Mapped[Optional["ModificationType"]] = relationship()





