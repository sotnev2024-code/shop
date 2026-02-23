import asyncio
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.bot import bot
from app.db.models.user import User


async def send_broadcast(
    db: AsyncSession,
    text: str,
    photo_url: Optional[str] = None,
) -> dict:
    """Send a broadcast message to all users."""
    result = await db.execute(select(User.telegram_id))
    user_ids = result.scalars().all()

    sent = 0
    failed = 0

    for uid in user_ids:
        try:
            if photo_url:
                await bot.send_photo(chat_id=uid, photo=photo_url, caption=text)
            else:
                await bot.send_message(chat_id=uid, text=text)
            sent += 1
            await asyncio.sleep(0.05)  # Rate limit
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(user_ids)}





