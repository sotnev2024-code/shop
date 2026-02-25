from __future__ import annotations

import asyncio
from typing import List, Optional
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.bot import get_bot
from app.config import settings
from app.db.models.user import User
from app.db.models.order import Order
from app.db.models.cart import CartItem
from app.db.models.favorite import Favorite


AudienceType = str  # "all" | "has_orders" | "has_cart" | "has_favorites" | "no_orders"


async def get_recipients(db: AsyncSession, audience: AudienceType) -> List[int]:
    """Return list of telegram_id for the given audience."""
    if audience == "all":
        result = await db.execute(select(User.telegram_id))
        return [row[0] for row in result.all()]

    if audience == "has_orders":
        subq = select(Order.user_id).distinct()
        result = await db.execute(
            select(User.telegram_id).where(User.id.in_(subq))
        )
        return [row[0] for row in result.all()]

    if audience == "has_cart":
        subq = select(CartItem.user_id).distinct()
        result = await db.execute(
            select(User.telegram_id).where(User.id.in_(subq))
        )
        return [row[0] for row in result.all()]

    if audience == "has_favorites":
        subq = select(Favorite.user_id).distinct()
        result = await db.execute(
            select(User.telegram_id).where(User.id.in_(subq))
        )
        return [row[0] for row in result.all()]

    if audience == "no_orders":
        subq = select(Order.user_id).distinct()
        result = await db.execute(
            select(User.telegram_id).where(User.id.not_in(subq))
        )
        return [row[0] for row in result.all()]

    # fallback: all
    result = await db.execute(select(User.telegram_id))
    return [row[0] for row in result.all()]


def _absolute_photo_url(image_url: str) -> str:
    """Build absolute URL for Telegram (send_photo needs http(s) URL)."""
    if not image_url:
        return ""
    if image_url.startswith("http://") or image_url.startswith("https://"):
        return image_url
    base = settings.public_base_url.strip()
    if not base:
        parsed = urlparse(settings.webapp_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
    return base.rstrip("/") + ("/" + image_url.lstrip("/"))


async def send_broadcast(
    db: AsyncSession,
    audience: AudienceType,
    text: str,
    photo_url: Optional[str] = None,
    button_text: Optional[str] = None,
    button_url: Optional[str] = None,
) -> dict:
    """Send a broadcast to the selected audience. Optional photo and inline button."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    telegram_ids = await get_recipients(db, audience)
    bot = get_bot()
    button_url = (button_url or "").strip() or settings.webapp_url
    reply_markup = None
    if button_text and button_text.strip():
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=button_text.strip(), url=button_url)]
            ]
        )

    sent = 0
    failed = 0
    abs_photo = _absolute_photo_url(photo_url) if photo_url else None

    for uid in telegram_ids:
        try:
            if abs_photo:
                await bot.send_photo(
                    chat_id=uid,
                    photo=abs_photo,
                    caption=text,
                    reply_markup=reply_markup,
                )
            else:
                await bot.send_message(
                    chat_id=uid,
                    text=text,
                    reply_markup=reply_markup,
                )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(telegram_ids)}
