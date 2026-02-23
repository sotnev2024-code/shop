from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.order import Order
from app.db.models.user import User


async def get_daily_stats(db: AsyncSession, days: int = 30) -> list[dict]:
    """Get daily order/revenue stats for the last N days."""
    start_date = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Order.created_at).label("date"),
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total), 0).label("revenue"),
        )
        .where(Order.created_at >= start_date)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )

    return [
        {
            "date": str(row.date),
            "orders": row.orders,
            "revenue": float(row.revenue),
        }
        for row in result.all()
    ]





