from __future__ import annotations

import logging

from app.bot.bot import get_bot, is_bot_configured
from app.config import settings

logger = logging.getLogger(__name__)


async def notify_new_order(
    order_id: int,
    customer_name: str,
    customer_phone: str,
    address: str | None,
    delivery_type: str | None,
    total: float,
    items_text: str,
    bonus_used: float = 0,
):
    """Send new order notification to admin chat."""
    if not is_bot_configured():
        logger.info(f"[DEV] Order #{order_id} created — bot not configured, skipping notification")
        return

    bot = get_bot()
    if not bot:
        return

    text = (
        f"📦 <b>Новый заказ #{order_id}</b>\n\n"
        f"👤 <b>Клиент:</b> {customer_name}\n"
        f"📱 <b>Телефон:</b> {customer_phone}\n"
    )

    if address:
        text += f"📍 <b>Адрес:</b> {address}\n"

    if delivery_type:
        delivery_label = "Самовывоз" if delivery_type == "pickup" else "Доставка"
        text += f"🚚 <b>Тип:</b> {delivery_label}\n"

    if bonus_used and bonus_used > 0:
        text += f"🎁 <b>Списано бонусов:</b> {int(bonus_used)}\n"

    text += f"\n🛒 <b>Товары:</b>\n{items_text}\n"
    text += f"\n💰 <b>Итого:</b> {total:.2f} ₽"

    await bot.send_message(
        chat_id=settings.admin_chat_id,
        text=text,
    )
