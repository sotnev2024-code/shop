from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings

logger = logging.getLogger(__name__)

bot: Bot | None = None
dp = Dispatcher()

# Cached bot profile photo bytes (fetched once on startup)
_bot_photo_bytes: bytes | None = None
_bot_photo_content_type: str = "image/jpeg"
_bot_username: str | None = None


def is_bot_configured() -> bool:
    """Check if a real bot token is set."""
    token = settings.bot_token
    return bool(token and token != "YOUR_BOT_TOKEN_HERE" and ":" in token)


def get_bot() -> Bot:
    """Create or return bot instance."""
    global bot
    if bot is None and is_bot_configured():
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return bot


def get_bot_photo_cache() -> tuple[bytes | None, str]:
    """Return cached bot photo bytes and content type."""
    return _bot_photo_bytes, _bot_photo_content_type


def get_bot_username() -> str | None:
    """Return cached bot username."""
    return _bot_username


async def fetch_and_cache_bot_photo():
    """Download the bot's profile photo and cache it in memory. Also cache username."""
    global _bot_photo_bytes, _bot_username
    b = get_bot()
    if not b:
        return
    try:
        me = await b.get_me()
        _bot_username = me.username
        logger.info(f"Bot username cached: @{_bot_username}")

        photos = await b.get_user_profile_photos(me.id, limit=1)
        if not photos.photos:
            logger.info("Bot has no profile photo")
            return

        # Get the largest available size (last in the list)
        best = photos.photos[0][-1]
        from io import BytesIO

        buf = BytesIO()
        await b.download(best.file_id, destination=buf)
        _bot_photo_bytes = buf.getvalue()
        logger.info(f"Bot profile photo cached ({len(_bot_photo_bytes)} bytes)")
    except Exception as e:
        logger.warning(f"Failed to fetch bot profile photo: {e}")


async def setup_bot():
    """Register all handlers and setup bot commands."""
    from aiogram.types import ErrorEvent
    from app.bot.handlers import start, orders as order_handlers, try_on
    from app.db.session import async_session
    from app.services.error_log_service import log_error, format_exception_traceback

    @dp.error()
    async def bot_error_handler(event: ErrorEvent):
        exc = event.exception
        logger.exception("Bot handler error: %s", exc)
        try:
            async with async_session() as db:
                await log_error(
                    db, str(exc), "ERROR",
                    path="bot", source="bot",
                    traceback_str=format_exception_traceback(exc),
                    extra={},
                )
        except Exception as log_exc:
            logger.debug("Failed to log bot error to DB: %s", log_exc)

    dp.include_router(start.router)
    dp.include_router(order_handlers.router)
    dp.include_router(try_on.router)

    # Cache bot photo
    await fetch_and_cache_bot_photo()
