import logging
import os
import re
from pathlib import Path
from typing import List, Optional

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
logger = logging.getLogger(__name__)

# Путь к backend/.env (независимо от текущей рабочей директории)
_BACKEND_DIR = Path(__file__).resolve().parents[3]
_ENV_FILE = _BACKEND_DIR / ".env"


def _read_admin_ids_from_env_file() -> List[int]:
    """Читаем ADMIN_IDS напрямую из backend/.env — на случай если Settings/os.environ не подхватили."""
    ids = []
    if not _ENV_FILE.exists():
        return ids
    try:
        raw = _ENV_FILE.read_text(encoding="utf-8", errors="ignore")
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip().upper() != "ADMIN_IDS":
                continue
            val = value.strip().strip("'\"").replace("\n", ",")
            for x in re.split(r"[,;\s]+", val):
                x = x.strip()
                if x:
                    try:
                        ids.append(int(x))
                    except ValueError:
                        pass
            break
    except Exception as e:
        logger.warning("Could not read ADMIN_IDS from %s: %s", _ENV_FILE, e)
    return ids


@router.get("/config", response_model=AppConfigResponse)
async def get_app_config(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return app configuration for the frontend."""
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()

    # Admin list: .env ADMIN_IDS (и из os.environ на случай если Settings не подхватил) + ID из БД
    def _parse_admin_ids(s: str) -> List[int]:
        out = []
        for x in (s or "").replace("\n", ",").split(","):
            raw = x.strip().strip('"\'')
            if not raw:
                continue
            try:
                out.append(int(raw))
            except (ValueError, TypeError):
                continue
        return out

    admin_ids_raw = getattr(config, "admin_ids", None) if config else None
    from_db = _parse_admin_ids(str(admin_ids_raw or ""))
    from_env = list(settings.admin_id_list)
    env_raw = os.environ.get("ADMIN_IDS") or os.environ.get("admin_ids") or ""
    from_env = list(dict.fromkeys(from_env + _parse_admin_ids(env_raw)))
    # Жёсткая подстраховка: читаем ADMIN_IDS прямо из backend/.env
    from_env_file = _read_admin_ids_from_env_file()
    from_env = list(dict.fromkeys(from_env + from_env_file))
    _admin_list = list(dict.fromkeys(from_env + from_db))
    try:
        uid = int(user.telegram_id)
    except (TypeError, ValueError):
        uid = None
    # Сравниваем и как int, и как str (на случай если где-то строка)
    is_admin = uid is not None and (uid in _admin_list or str(uid) in [str(x) for x in _admin_list])
    logger.info(
        "Config: telegram_id=%s, admin_list=%s, from_env_file=%s, env_file_path=%s, is_admin=%s",
        user.telegram_id,
        _admin_list,
        from_env_file,
        str(_ENV_FILE),
        is_admin,
    )
    is_owner = (
        settings.dev_mode
        or (settings.owner_id != 0 and user.telegram_id == settings.owner_id)
    )

    # Check if bot photo is available; use absolute URL if public_base_url is set (for Mini App)
    photo_bytes, _ = get_bot_photo_cache()
    if photo_bytes:
        base = (getattr(settings, "public_base_url", None) or "").strip().rstrip("/")
        bot_photo_url = f"{base}/api/v1/bot-photo" if base else "/api/v1/bot-photo"
    else:
        bot_photo_url = None
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
            current_telegram_id=user.telegram_id,
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
        current_telegram_id=user.telegram_id,
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
