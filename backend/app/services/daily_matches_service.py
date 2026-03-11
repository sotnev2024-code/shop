"""Daily matches notification to forum chat."""

from __future__ import annotations

import logging
from datetime import date, datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.bot import get_bot, is_bot_configured
from app.config import settings
from app.db.models.app_config import AppConfig

logger = logging.getLogger(__name__)


def _format_match_time(d: str | None) -> str:
    """Extract HH:MM from ISO datetime string."""
    if not d:
        return ""
    try:
        dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return ""


async def send_daily_matches(db: AsyncSession) -> bool:
    """
    Fetch today's matches, format message from template, and send to forum.
    Returns True if sent, False otherwise.
    """
    if not is_bot_configured():
        logger.info("[DEV] Daily matches job — bot not configured, skipping")
        return False

    bot = get_bot()
    if not bot:
        return False

    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    chat_id_raw = getattr(config, "daily_matches_forum_chat_id", None) if config else None
    if not chat_id_raw or not str(chat_id_raw).strip():
        logger.info("Daily matches: no forum chat_id configured, skipping")
        return False

    chat_id = chat_id_raw.strip()
    try:
        if chat_id.lstrip("-").isdigit():
            chat_id = int(chat_id)
    except (ValueError, TypeError):
        pass

    topic_id = None
    topic_raw = getattr(config, "daily_matches_forum_topic_id", None) if config else None
    if topic_raw and str(topic_raw).strip():
        try:
            topic_id = int(topic_raw.strip())
        except (ValueError, TypeError):
            pass

    # Fetch today's matches (avoid HTTPException by catching)
    try:
        from app.api.v1.football import _fetch_popular_fixtures

        data = await _fetch_popular_fixtures(from_date=date.today(), days_ahead=0)
    except Exception as e:
        logger.warning("Daily matches: failed to fetch fixtures: %s", e)
        return False

    matches = data.get("matches") or []
    today_str = date.today().strftime("%d.%m.%Y")

    matches_parts = []
    for m in matches:
        league = (m.get("league") or {}).get("name") or "?"
        home = (m.get("home_team") or {}).get("name") or "?"
        away = (m.get("away_team") or {}).get("name") or "?"
        time_str = _format_match_time(m.get("date"))
        matches_parts.append(f"• {league}: {home} — {away}" + (f" ({time_str})" if time_str else ""))

    matches_list = "\n".join(matches_parts) if matches_parts else "Матчей на сегодня нет."
    shop_name = (config.shop_name if config else None) or settings.shop_name or "Магазин"

    from app.services.bot_message_service import get_template, substitute_variables

    template = await get_template(db, "daily_matches")
    text_template = template.get("text", "⚽ Матчи на {date}\n\n{matches_list}")
    if not text_template:
        return False

    context = {
        "date": today_str,
        "matches_list": matches_list,
        "matches_count": str(len(matches)),
        "shop_name": shop_name,
    }
    text = substitute_variables(text_template, context)

    # Build InlineKeyboard from buttons
    reply_markup = None
    buttons_config = template.get("buttons") or []
    if buttons_config and isinstance(buttons_config, list):
        rows = []
        for row in buttons_config:
            if not isinstance(row, list):
                continue
            btn_row = []
            for btn in row:
                if not isinstance(btn, dict):
                    continue
                t = btn.get("text") or ""
                u = btn.get("url") or ""
                if t and u:
                    btn_row.append(InlineKeyboardButton(text=str(t), url=str(u)))
            if btn_row:
                rows.append(btn_row)
        if rows:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=rows)

    send_kw = {"chat_id": chat_id, "text": text}
    if topic_id is not None:
        send_kw["message_thread_id"] = topic_id
    if reply_markup:
        send_kw["reply_markup"] = reply_markup

    try:
        await bot.send_message(**send_kw)
        logger.info("Daily matches sent to forum (chat_id=%s)", chat_id)
        return True
    except Exception as e:
        logger.warning("Daily matches: failed to send: %s", e)
        return False
