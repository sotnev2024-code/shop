from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    photo_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    button_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    button_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    button_color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # blue, green, red, gray
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    channel_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    product: Mapped[Optional["Product"]] = relationship(back_populates="posts")
