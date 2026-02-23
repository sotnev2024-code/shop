from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    promo_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("promo_codes.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="new")
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    bonus_used: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    delivery_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    delivery_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    customer_name: Mapped[str] = mapped_column(String(255), default="")
    customer_phone: Mapped[str] = mapped_column(String(50), default="")
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_coords: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    payment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    delivery_service: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    promo_code: Mapped["PromoCode | None"] = relationship()


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    price_at_order: Mapped[float] = mapped_column(Numeric(10, 2))
    modification_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("modification_types.id", ondelete="SET NULL"), nullable=True, index=True
    )
    modification_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
    modification_type: Mapped["ModificationType | None"] = relationship()





