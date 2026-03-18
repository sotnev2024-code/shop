"""Autopost products to Telegram channel on schedule."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.models.app_config import AppConfig
from app.db.models.product import Product
from app.db.models.product_variant import ProductVariant
from app.services.post_service import (
        send_post_to_channel,
        _absolute_photo_url,
        _build_product_url,
    )
from app.services.bot_message_service import substitute_variables

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE = """<b>{product_name}</b>

{product_description}

Цена: {product_price}

{modification_block}
Заказать можно по кнопке ниже👇"""


def _get_product_image_url(product: Product) -> Optional[str]:
    """Get first image URL from product (media or image_url)."""
    if product.media:
        for m in sorted(product.media, key=lambda x: x.sort_order):
            if m.media_type == "image" and m.file_path:
                return m.file_path
    return product.image_url


def _build_product_context(
    product: Product,
    shop_name: str,
    product_url: str,
    hide_price: bool,
) -> Dict[str, Any]:
    """Build template context for a product."""
    desc = (product.description or "").strip() or "—"
    if hide_price:
        price_display = "Цена скрыта"
    else:
        price_display = f"{product.price:,.0f} ₽"

    mod_name = ""
    mod_values = ""
    if product.variants and len(product.variants) > 0:
        v0 = product.variants[0]
        mod_type = getattr(v0, "modification_type", None)
        if mod_type:
            mod_name = mod_type.name
        mod_values = ", ".join(v.value for v in product.variants)

    if mod_name and mod_values:
        modification_block = f"{mod_name}: {mod_values}"
    else:
        modification_block = ""

    return {
        "product_name": product.name,
        "product_description": desc,
        "product_price": price_display,
        "modification_name": mod_name,
        "modification_values": mod_values,
        "modification_block": modification_block,
        "product_url": product_url,
        "shop_name": shop_name,
    }


async def run_autopost(db: AsyncSession) -> bool:
    """
    Post one product to the channel (rotation). Called by scheduler.
    Returns True if a post was sent, False otherwise.
    """
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        return False
    if not getattr(config, "autopost_enabled", False):
        return False
    channel_id = (getattr(config, "channel_id", None) or "").strip()
    if not channel_id:
        channel_id = (getattr(settings, "channel_id", None) or "").strip()
    if not channel_id:
        logger.warning("Autopost skipped: channel_id not configured")
        return False

    shop_name = getattr(config, "shop_name", None) or settings.shop_name or "Магазин"

    # Load products: available, with image
    products_result = await db.execute(
        select(Product)
        .where(Product.is_available == True)
        .options(
            selectinload(Product.media),
            selectinload(Product.variants).selectinload(ProductVariant.modification_type),
        )
    )
    products: List[Product] = list(products_result.scalars().all())

    # Filter: must have image
    products_with_image: List[Product] = []
    for p in products:
        if _get_product_image_url(p):
            products_with_image.append(p)

    if not products_with_image:
        logger.warning("Autopost skipped: no products with images")
        return False

    last_idx = getattr(config, "autopost_last_product_index", 0) or 0
    product = products_with_image[last_idx % len(products_with_image)]
    next_idx = (last_idx + 1) % len(products_with_image)

    product_url = _build_product_url(product.id)
    hide_price = getattr(config, "autopost_hide_price", False)
    context = _build_product_context(product, shop_name, product_url, hide_price)

    template = getattr(config, "autopost_template", None) or DEFAULT_TEMPLATE
    text = substitute_variables(template, context)

    button_text = getattr(config, "autopost_button_text", None) or "Заказать"
    button_color = getattr(config, "autopost_button_color", None) or "green"
    photo_url = _get_product_image_url(product)

    if not photo_url:
        return False

    # Make photo URL absolute for Telegram
    photo_url = _absolute_photo_url(photo_url or "")
    if not photo_url:
        logger.warning("Autopost skipped: could not build absolute photo URL")
        return False

    try:
        await send_post_to_channel(
            channel_id=channel_id,
            text=text,
            photo_url=photo_url,
            button_text=button_text,
            button_url=product_url,
            button_color=button_color,
        )
        config.autopost_last_product_index = next_idx
        await db.commit()
        logger.info(f"Autopost sent: product {product.id} ({product.name})")
        return True
    except Exception as e:
        logger.error(f"Autopost failed: {e}", exc_info=True)
        await db.rollback()
        return False
