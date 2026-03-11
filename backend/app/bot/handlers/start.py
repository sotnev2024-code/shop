import logging

from aiogram import Router, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

from app.config import settings
from app.db.session import async_session
from app.services.bot_message_service import get_template, substitute_variables

logger = logging.getLogger(__name__)

router = Router()


def _make_webapp_button(text: str, url: str, style: str | None = None):
    """Create InlineKeyboardButton with WebApp. Style may not be supported for WebApp in all clients."""
    kwargs = {"text": text, "web_app": WebAppInfo(url=url)}
    if style:
        kwargs["style"] = style
    try:
        return InlineKeyboardButton(**kwargs)
    except TypeError:
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))


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

    # Welcome message (no product)
    async with async_session() as db:
        tpl = await get_template(db, "welcome")
        text = substitute_variables(
            tpl.get("text", ""),
            {
                "user_name": (message.from_user and message.from_user.first_name) or "Пользователь",
                "shop_name": settings.shop_name,
            },
        )
        btn_text = tpl.get("button_text") or "🛍 Открыть магазин"
        btn_style = tpl.get("button_style")

    btn = _make_webapp_button(btn_text, webapp_url, btn_style)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn]])
    await message.answer(text, reply_markup=keyboard)


async def _send_product_message(message: types.Message, product_id: int, webapp_url: str):
    """Send product info with image and a button to open it in the Mini App."""
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.db.models.product import Product

        async with async_session() as db:
            result = await db.execute(
                select(Product)
                .where(Product.id == product_id)
                .options(
                    selectinload(Product.categories),
                    selectinload(Product.media),
                )
            )
            product = result.scalar_one_or_none()

        if not product:
            async with async_session() as db:
                tpl = await get_template(db, "product_not_found")
                text = substitute_variables(
                    tpl.get("text", ""),
                    {"shop_name": settings.shop_name},
                )
            await message.answer(text)
            return

        # Build context for product template
        cat_names = ", ".join(c.name for c in product.categories) if product.categories else ""
        desc = ""
        if product.description:
            desc = product.description[:200]
            if len(product.description) > 200:
                desc += "..."
        old_price_line = f"<s>{product.old_price:,.0f} ₽</s>" if product.old_price else ""
        stock_warning = "\n⚠️ Нет в наличии" if product.stock_quantity <= 0 else ""

        context = {
            "product_name": product.name,
            "product_categories": cat_names,
            "product_price": f"{product.price:,.0f} ₽",
            "product_old_price": f"{product.old_price:,.0f} ₽" if product.old_price else "",
            "product_old_price_line": old_price_line,
            "product_description": desc,
            "product_stock_warning": stock_warning,
            "shop_name": settings.shop_name,
        }

        async with async_session() as db:
            tpl = await get_template(db, "product")

        template_str = tpl.get("template") or "<b>{product_name}</b>\n📂 {product_categories}\n💰 <b>{product_price}</b>"
        text = substitute_variables(template_str, context)

        product_url = f"{webapp_url}/product/{product_id}"
        btn_product_text = tpl.get("button_product_text") or "🔍 Посмотреть товар"
        btn_shop_text = tpl.get("button_shop_text") or "🛍 Открыть магазин"
        btn_product_style = tpl.get("button_product_style")
        btn_shop_style = tpl.get("button_shop_style")

        btn1 = _make_webapp_button(btn_product_text, product_url, btn_product_style)
        btn2 = _make_webapp_button(btn_shop_text, webapp_url, btn_shop_style)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn1], [btn2]])

        # Try to send with photo
        image_url = None
        if product.media:
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

        await message.answer(text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error sending product message: {e}", exc_info=True)
        async with async_session() as db:
            tpl = await get_template(db, "error")
            err_text = substitute_variables(
                tpl.get("text", "Произошла ошибка. Попробуйте позже."),
                {"shop_name": settings.shop_name},
            )
        await message.answer(err_text)
