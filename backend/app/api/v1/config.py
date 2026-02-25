from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models.app_config import AppConfig
from app.db.models.user import User
from app.api.deps import get_current_user
from app.schemas.config import AppConfigResponse
from app.bot.bot import is_bot_configured, get_bot_photo_cache, get_bot_username

router = APIRouter()


@router.get("/config", response_model=AppConfigResponse)
async def get_app_config(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return app configuration for the frontend."""
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()

    # Admin list: .env ADMIN_IDS всегда в доступе + ID из БД (раздел «Администраторы»)
    admin_ids_raw = getattr(config, "admin_ids", None) if config else None
    from_db = [int(x.strip()) for x in str(admin_ids_raw or "").split(",") if x.strip()]
    from_env = settings.admin_id_list
    _admin_list = list(dict.fromkeys(from_env + from_db))
    is_admin = user.telegram_id in _admin_list
    is_owner = (
        settings.dev_mode
        or (settings.owner_id != 0 and user.telegram_id == settings.owner_id)
    )

    # Check if bot photo is available
    photo_bytes, _ = get_bot_photo_cache()
    bot_photo_url = "/api/v1/bot-photo" if photo_bytes else None
    bot_username = get_bot_username()

    if config is None:
        # Return defaults from .env
        return AppConfigResponse(
            shop_name=settings.shop_name,
            checkout_type=settings.checkout_type.value,
            product_source=settings.product_source.value,
            delivery_enabled=settings.delivery_enabled,
            pickup_enabled=settings.pickup_enabled,
            promo_enabled=settings.promo_enabled,
            mailing_enabled=settings.mailing_enabled,
            currency="RUB",
            yandex_maps_enabled=bool(settings.yandex_maps_key),
            yandex_maps_key=settings.yandex_maps_key,
            payment_enabled=bool(settings.payment_provider_token),
            support_link=settings.support_link,
            is_admin=is_admin,
            is_owner=is_owner,
            bot_photo_url=bot_photo_url,
            bot_username=bot_username,
            store_address=None,
            delivery_city=None,
            delivery_cost=0,
            free_delivery_min_amount=0,
            min_order_amount_pickup=0,
            min_order_amount_delivery=0,
            banner_aspect_shape="rectangle",
            banner_size="medium",
            category_image_size="medium",
            bonus_enabled=False,
            bonus_welcome_enabled=False,
            bonus_welcome_amount=0,
            bonus_purchase_enabled=False,
            bonus_purchase_percent=0,
            bonus_spend_enabled=False,
            bonus_spend_limit_type="percent",
            bonus_spend_limit_value=0,
        )

    # If no store address, force pickup off
    pickup_enabled = config.pickup_enabled
    if not config.store_address:
        pickup_enabled = False

    # Read integration keys from DB first, fall back to .env
    yandex_maps_key = config.yandex_maps_key or settings.yandex_maps_key
    payment_token = config.payment_provider_token or settings.payment_provider_token
    support_link = config.support_link or settings.support_link

    return AppConfigResponse(
        shop_name=config.shop_name,
        checkout_type=config.checkout_type,
        product_source=config.product_source,
        delivery_enabled=config.delivery_enabled,
        pickup_enabled=pickup_enabled,
        promo_enabled=config.promo_enabled,
        mailing_enabled=config.mailing_enabled,
        currency=config.currency,
        yandex_maps_enabled=bool(yandex_maps_key),
        yandex_maps_key=yandex_maps_key,
        payment_enabled=bool(payment_token),
        support_link=support_link or "",
        is_admin=is_admin,
        is_owner=is_owner,
        bot_photo_url=bot_photo_url,
        bot_username=bot_username,
        store_address=config.store_address,
        delivery_city=config.delivery_city,
        delivery_cost=float(getattr(config, "delivery_cost", 0)),
        free_delivery_min_amount=float(getattr(config, "free_delivery_min_amount", 0)),
        min_order_amount_pickup=float(getattr(config, "min_order_amount_pickup", 0)),
        min_order_amount_delivery=float(getattr(config, "min_order_amount_delivery", 0)),
        banner_aspect_shape=getattr(config, "banner_aspect_shape", "rectangle"),
        banner_size=getattr(config, "banner_size", "medium"),
        category_image_size=getattr(config, "category_image_size", "medium"),
        bonus_enabled=getattr(config, "bonus_enabled", False),
        bonus_welcome_enabled=getattr(config, "bonus_welcome_enabled", False),
        bonus_welcome_amount=float(getattr(config, "bonus_welcome_amount", 0)),
        bonus_purchase_enabled=getattr(config, "bonus_purchase_enabled", False),
        bonus_purchase_percent=float(getattr(config, "bonus_purchase_percent", 0)),
        bonus_spend_enabled=getattr(config, "bonus_spend_enabled", False),
        bonus_spend_limit_type=getattr(config, "bonus_spend_limit_type", "percent"),
        bonus_spend_limit_value=float(getattr(config, "bonus_spend_limit_value", 0)),
    )


@router.get("/bot-photo")
async def get_bot_photo():
    """Return the bot's profile photo (cached on startup)."""
    photo_bytes, content_type = get_bot_photo_cache()
    if not photo_bytes:
        return Response(status_code=404)
    return Response(
        content=photo_bytes,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )
