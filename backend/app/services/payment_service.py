"""
Payment service via Telegram Payments API.
"""

from aiogram.types import LabeledPrice

from app.bot.bot import bot
from app.config import settings


async def send_invoice(
    chat_id: int,
    order_id: int,
    title: str,
    description: str,
    amount: int,  # In kopecks (cents)
    currency: str = "RUB",
) -> None:
    """Send a payment invoice to user via Telegram bot."""
    if not settings.payment_provider_token:
        raise ValueError("Payment provider token not configured")

    prices = [LabeledPrice(label=title, amount=amount)]

    await bot.send_invoice(
        chat_id=chat_id,
        title=title,
        description=description,
        payload=f"order_{order_id}",
        provider_token=settings.payment_provider_token,
        currency=currency,
        prices=prices,
        start_parameter=f"order-{order_id}",
    )





