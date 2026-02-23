from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ModificationValue(Base):
    """Predefined value for a modification type (e.g. Size -> S, M, L)."""
    __tablename__ = "modification_values"
    __table_args__ = (
        UniqueConstraint(
            "modification_type_id", "value",
            name="uq_modification_value_type_value",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    modification_type_id: Mapped[int] = mapped_column(
        ForeignKey("modification_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    modification_type: Mapped["ModificationType"] = relationship(
        back_populates="values",
    )
