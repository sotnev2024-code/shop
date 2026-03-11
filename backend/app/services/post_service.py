from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.bot.bot import get_bot, get_bot_username
from app.config import settings


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


def _build_product_deeplink(product_id: int) -> str:
    """Build t.me deep link for product: https://t.me/<bot_username>?start=product_<id>."""
    username = get_bot_username()
    if not username:
        return settings.webapp_url + f"/product/{product_id}"
    return f"https://t.me/{username}?start=product_{product_id}"


def _build_shop_deeplink() -> str:
    """Build t.me deep link for shop: https://t.me/<bot_username>?start=start or webapp_url."""
    username = get_bot_username()
    if not username:
        return settings.webapp_url
    return f"https://t.me/{username}?start=start"


def _color_to_style(button_color: Optional[str]) -> Optional[str]:
    """Map our color names to aiogram InlineKeyboardButton style (primary, success, danger)."""
    if not button_color:
        return None
    c = str(button_color).lower()
    if c == "blue":
        return "primary"
    if c == "green":
        return "success"
    if c == "red":
        return "danger"
    # gray or other — omit style (app-specific default)
    return None


async def send_post_to_channel(
    channel_id: str,
    text: str,
    photo_url: Optional[str] = None,
    photo_file_id: Optional[str] = None,
    button_text: Optional[str] = None,
    button_url: Optional[str] = None,
    button_color: Optional[str] = None,
) -> int:
    """
    Send a post to a Telegram channel.
    Returns the message_id of the sent message.
    Raises ValueError if channel not configured or bot not ready.
    """
    channel_id = (channel_id or "").strip()
    if not channel_id:
        raise ValueError("Channel not configured")

    bot = get_bot()
    if not bot:
        raise ValueError("Bot not initialized")

    reply_markup = None
    btn_text = (button_text or "").strip()
    btn_url = (button_url or "").strip()
    if btn_text and btn_url:
        style = _color_to_style(button_color)
        # Build button dict: style is in Telegram API 7.x, aiogram 3.13 may not have it
        btn_dict = {"text": btn_text, "url": btn_url}
        if style:
            btn_dict["style"] = style
        btn = InlineKeyboardButton.model_validate(btn_dict)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[[btn]])

    abs_photo = _absolute_photo_url(photo_url) if photo_url else None

    if photo_file_id:
        msg = await bot.send_photo(
            chat_id=channel_id,
            photo=photo_file_id,
            caption=text or None,
            reply_markup=reply_markup,
        )
    elif abs_photo:
        msg = await bot.send_photo(
            chat_id=channel_id,
            photo=abs_photo,
            caption=text or None,
            reply_markup=reply_markup,
        )
    else:
        msg = await bot.send_message(
            chat_id=channel_id,
            text=text or "(пусто)",
            reply_markup=reply_markup,
        )

    return msg.message_id
