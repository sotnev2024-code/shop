from __future__ import annotations

from typing import List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ModificationType(Base):
    __tablename__ = "modification_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    values: Mapped[List["ModificationValue"]] = relationship(
        back_populates="modification_type",
        cascade="all, delete-orphan",
        order_by="ModificationValue.sort_order",
    )
    product_variants: Mapped[List["ProductVariant"]] = relationship(
        back_populates="modification_type", cascade="all, delete-orphan"
    )
