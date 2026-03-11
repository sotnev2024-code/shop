"""Competition (football) bets: user predictions with outcome and amount."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CompetitionBet(Base):
    __tablename__ = "competition_bets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    fixture_id: Mapped[int] = mapped_column(BigInteger, index=True)  # API-Football fixture id
    match_label: Mapped[str] = mapped_column(String(255), default="")  # "Home - Away" for display
    outcome: Mapped[str] = mapped_column(String(4), default="")  # H, D, A
    amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    odds: Mapped[float] = mapped_column(Numeric(8, 4), default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, won, lost
    payout: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="competition_bets")
