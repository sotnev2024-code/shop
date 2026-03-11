from __future__ import annotations

import html
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.bot import get_bot, is_bot_configured
from app.config import settings
from app.db.models.app_config import AppConfig
from app.db.models.order import Order
from app.db.models.user import User

logger = logging.getLogger(__name__)


def _escape(s: str) -> str:
    """Escape HTML in user-provided strings."""
    return html.escape(str(s)) if s else ""


async def notify_new_order(
    db: AsyncSession,
    user: User,
    order: Order,
):
    """Send new order notification to admin chat."""
    if not is_bot_configured():
        logger.info(f"[DEV] Order #{order.id} created — bot not configured, skipping notification")
        return

    bot = get_bot()
    if not bot:
        return

    # Resolve chat_id: AppConfig takes precedence over .env
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    chat_id_raw = getattr(config, "order_notification_chat_id", None) if config else None
    if chat_id_raw and str(chat_id_raw).strip():
        chat_id = chat_id_raw.strip()
        try:
            if chat_id.lstrip("-").isdigit():
                chat_id = int(chat_id)
        except (ValueError, TypeError):
            pass
    else:
        chat_id = settings.admin_chat_id

    if not chat_id:
        logger.info("[DEV] No chat_id for order notifications, skipping")
        return

    # Build user link: tg username or tg://user?id=
    name_escaped = _escape(order.customer_name)
    if user.username:
        user_link = f'<a href="https://t.me/{_escape(user.username)}">{name_escaped}</a>'
    else:
        user_link = f'<a href="tg://user?id={user.telegram_id}">{name_escaped}</a>'

    username_str = f"@{_escape(user.username)}" if user.username else "—"
    text = (
        f"📦 <b>Новый заказ #{order.id}</b>\n\n"
        f"👤 <b>Пользователь:</b> {user_link}\n"
        f"🆔 <b>id:</b> {user.telegram_id}\n"
        f"📛 <b>username:</b> {username_str}\n"
        f"📱 <b>Номер телефона:</b> {_escape(order.customer_phone)}\n"
    )

    # Delivery
    if order.delivery_type:
        delivery_label = "Самовывоз" if order.delivery_type == "pickup" else "Доставка"
        text += f"🚚 <b>Способ доставки:</b> {delivery_label}\n"

    text += f"📍 <b>Адрес:</b> {_escape(order.address) or '—'}\n"
    text += f"💰 <b>Сумма:</b> {float(order.total):.2f} ₽\n"

    # Info: discount, promo, bonus
    info_parts = []
    if order.promo_code_id and order.promo_code:
        pc = order.promo_code
        if pc.discount_type == "free_delivery":
            info_parts.append(f"Бесплатная доставка по промокоду {_escape(pc.code)}")
        else:
            info_parts.append(f"Скидка по промокоду {_escape(pc.code)}")
    if order.discount and float(order.discount) > 0:
        info_parts.append(f"Скидка: {float(order.discount):.2f} ₽")
    if order.bonus_used and float(order.bonus_used) > 0:
        info_parts.append(f"Списано бонусов: {int(order.bonus_used)}")
    if info_parts:
        text += f"ℹ️ <b>Информация:</b> {', '.join(info_parts)}\n"

    # Items
    items_parts = []
    for item in order.items:
        label = ""
        if item.modification_type and item.modification_value:
            label = f" ({item.modification_type.name}: {_escape(item.modification_value)})"
        line_total = float(item.price_at_order) * item.quantity
        items_parts.append(
            f"  • {_escape(item.product.name)}{label} x{item.quantity} — {line_total:.2f} ₽"
        )
    text += f"\n🛒 <b>Товары:</b>\n" + "\n".join(items_parts)

    # Extra fields if present
    if order.delivery_fee and float(order.delivery_fee) > 0:
        text += f"\n🚚 <b>Стоимость доставки:</b> {float(order.delivery_fee):.2f} ₽"
    if order.delivery_service:
        text += f"\n📦 <b>Служба доставки:</b> {_escape(order.delivery_service)}"
    if order.payment_status:
        text += f"\n💳 <b>Статус оплаты:</b> {_escape(order.payment_status)}"
    if order.tracking_number:
        text += f"\n📍 <b>Трек-номер:</b> {_escape(order.tracking_number)}"

    await bot.send_message(
        chat_id=chat_id,
        text=text,
    )


async def notify_user_order_status_changed(
    db: AsyncSession,
    order: Order,
    new_status: str,
):
    """Send order status change notification to the user who placed the order."""
    if not order.user:
        return
    user = order.user
    if not is_bot_configured():
        logger.info(f"[DEV] Order #{order.id} status changed — bot not configured, skipping user notification")
        return

    bot = get_bot()
    if not bot:
        return

    from app.services.bot_message_service import (
        get_template,
        substitute_variables,
        get_order_status_label,
    )
    from app.db.models.app_config import AppConfig

    config_result = await db.execute(select(AppConfig).limit(1))
    app_config = config_result.scalar_one_or_none()
    shop_name = (app_config.shop_name if app_config else None) or settings.shop_name or "Магазин"

    template = await get_template(db, "order_status_changed")
    text_template = template.get("text", "Статус вашего заказа #{order_id} изменён на: {order_status}")
    if not text_template:
        return

    context = {
        "order_id": str(order.id),
        "order_status": new_status,
        "order_status_label": get_order_status_label(new_status),
        "shop_name": shop_name,
        "user_name": user.first_name or order.customer_name or "Покупатель",
        "tracking_number": order.tracking_number or "",
    }
    text = substitute_variables(text_template, context)
    if not text.strip():
        return

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text,
        )
    except Exception as e:
        logger.warning("Failed to send order status notification to user %s: %s", user.telegram_id, e)
