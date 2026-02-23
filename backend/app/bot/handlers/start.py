import logging

from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

from app.config import settings

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    """Handle /start command — show Mini App button or product info via deep link."""
    webapp_url = settings.webapp_url
    payload = command.args  # e.g. "product_12"

    # Deep link: /start product_<id>
    if payload and payload.startswith("product_"):
        try:
            product_id = int(payload.replace("product_", ""))
        except (ValueError, TypeError):
            product_id = None

        if product_id:
            await _send_product_message(message, product_id, webapp_url)
            return

    # Default welcome message
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 Открыть магазин",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ]
    )
    await message.answer(
        "Добро пожаловать! Нажмите кнопку ниже, чтобы открыть магазин 👇",
        reply_markup=keyboard,
    )


async def _send_product_message(message: types.Message, product_id: int, webapp_url: str):
    """Send product info with image and a button to open it in the Mini App."""
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.session import async_session
        from app.db.models.product import Product

        async with async_session() as db:
            result = await db.execute(
                select(Product)
                .where(Product.id == product_id)
                .options(
                    selectinload(Product.category),
                    selectinload(Product.media),
                )
            )
            product = result.scalar_one_or_none()

        if not product:
            await message.answer("Товар не найден 😔")
            return

        # Build text
        text_parts = [f"<b>{product.name}</b>"]
        if product.category:
            text_parts.append(f"📂 {product.category.name}")
        text_parts.append(f"💰 <b>{product.price:,.0f} ₽</b>")
        if product.old_price:
            text_parts.append(f"<s>{product.old_price:,.0f} ₽</s>")
        if product.description:
            desc = product.description[:200]
            if len(product.description) > 200:
                desc += "..."
            text_parts.append(f"\n{desc}")

        if product.stock_quantity <= 0:
            text_parts.append("\n⚠️ Нет в наличии")

        text = "\n".join(text_parts)

        # Button to open product in Mini App
        product_url = f"{webapp_url}/product/{product_id}"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔍 Посмотреть товар",
                        web_app=WebAppInfo(url=product_url),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🛍 Открыть магазин",
                        web_app=WebAppInfo(url=webapp_url),
                    )
                ],
            ]
        )

        # Try to send with photo
        image_url = None
        if product.media:
            # Get first image
            for m in sorted(product.media, key=lambda x: x.sort_order):
                if m.media_type == "image":
                    image_url = m.file_path
                    break
        if not image_url and product.image_url:
            image_url = product.image_url

        if image_url and image_url.startswith("http"):
            try:
                await message.answer_photo(
                    photo=image_url,
                    caption=text,
                    reply_markup=keyboard,
                )
                return
            except Exception as e:
                logger.warning(f"Failed to send photo for product {product_id}: {e}")

        # Fallback: text only
        await message.answer(
            text,
            reply_markup=keyboard,
        )

    except Exception as e:
        logger.error(f"Error sending product message: {e}", exc_info=True)
        await message.answer("Произошла ошибка. Попробуйте позже.")
