"""Competition points movements: bonus, bet placed, bet win, etc."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitionAccrual(Base):
    __tablename__ = "competition_accruals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))  # positive = credit, negative = bet
    kind: Mapped[str] = mapped_column(String(50), default="")  # monthly_bonus, bet_placed, bet_win
    description: Mapped[str] = mapped_column(String(500), default="")
    bet_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # FK to competition_bets if applicable
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="competition_accruals")
