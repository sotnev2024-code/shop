from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.bonus_transaction import BonusTransaction
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(
    user: User = Depends(get_current_user),
):
    """Current user profile (e.g. bonus balance)."""
    return {
        "bonus_balance": float(user.bonus_balance or 0),
    }


@router.get("/bonus-transactions")
async def get_bonus_transactions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Last bonus transactions for the current user."""
    result = await db.execute(
        select(BonusTransaction)
        .where(BonusTransaction.user_id == user.id)
        .order_by(BonusTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.scalars().all()
    return {
        "items": [
            {
                "id": tx.id,
                "amount": float(tx.amount),
                "kind": tx.kind,
                "order_id": tx.order_id,
                "created_at": tx.created_at.isoformat() if isinstance(tx.created_at, datetime) else tx.created_at,
            }
            for tx in rows
        ],
    }
