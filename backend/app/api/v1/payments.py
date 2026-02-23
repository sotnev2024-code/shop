from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models.order import Order
from app.db.models.user import User
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/payments/create/{order_id}")
async def create_payment(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a payment link for an order via Telegram Payments."""
    if not settings.payment_provider_token:
        raise HTTPException(status_code=400, detail="Payments not configured")

    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Order already paid")

    # Telegram Payments are processed through the bot using sendInvoice
    # The frontend will use the Telegram Mini App payment API
    return {
        "order_id": order.id,
        "amount": float(order.total),
        "currency": "RUB",
        "provider_token": settings.payment_provider_token,
        "title": f"Заказ #{order.id}",
        "description": f"Оплата заказа #{order.id}",
    }


@router.post("/payments/confirm/{order_id}")
async def confirm_payment(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Confirm payment for an order (called after successful Telegram payment)."""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.user_id == user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.payment_status = "paid"
    order.status = "paid"
    await db.commit()

    return {"ok": True, "status": "paid"}





