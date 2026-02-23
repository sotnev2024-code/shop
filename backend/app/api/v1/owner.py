"""Owner (super-admin / platform seller) endpoints.

Only accessible to the user whose Telegram ID matches OWNER_ID in .env.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models.app_config import AppConfig
from app.db.models.user import User
from app.api.deps import get_owner_user
from app.schemas.config import OwnerConfigResponse, OwnerConfigUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def _mask_secret(value: str | None) -> str | None:
    """Mask a secret value for safe display, showing first 4 and last 4 chars."""
    if not value:
        return None
    if len(value) <= 10:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


async def _get_or_create_config(db: AsyncSession) -> AppConfig:
    """Fetch the single AppConfig row or create it with .env defaults."""
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    if config is None:
        config = AppConfig(
            shop_name=settings.shop_name,
            checkout_type=settings.checkout_type.value,
            product_source=settings.product_source.value,
            delivery_enabled=settings.delivery_enabled,
            pickup_enabled=settings.pickup_enabled,
            promo_enabled=settings.promo_enabled,
            mailing_enabled=settings.mailing_enabled,
            currency="RUB",
            moysklad_token=settings.moysklad_token,
            one_c_endpoint=settings.one_c_endpoint,
            one_c_login=settings.one_c_login,
            one_c_password=settings.one_c_password,
            payment_provider_token=settings.payment_provider_token,
            yandex_maps_key=settings.yandex_maps_key,
            support_link=settings.support_link or None,
            sync_interval_minutes=settings.sync_interval_minutes,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


@router.get("/config", response_model=OwnerConfigResponse)
async def owner_get_config(
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_owner_user),
):
    """Return full platform configuration for the owner.

    Secret tokens are masked for display safety.
    """
    config = await _get_or_create_config(db)

    return OwnerConfigResponse(
        checkout_type=config.checkout_type,
        product_source=config.product_source,
        promo_enabled=config.promo_enabled,
        mailing_enabled=config.mailing_enabled,
        delivery_enabled=config.delivery_enabled,
        pickup_enabled=config.pickup_enabled,
        delivery_sdek_enabled=config.delivery_sdek_enabled,
        delivery_pochta_enabled=config.delivery_pochta_enabled,
        delivery_yandex_enabled=config.delivery_yandex_enabled,
        moysklad_token=_mask_secret(config.moysklad_token),
        one_c_endpoint=config.one_c_endpoint,
        one_c_login=config.one_c_login,
        one_c_password=_mask_secret(config.one_c_password),
        payment_provider_token=_mask_secret(config.payment_provider_token),
        yandex_maps_key=_mask_secret(config.yandex_maps_key),
        support_link=config.support_link,
        sync_interval_minutes=config.sync_interval_minutes,
    )


@router.patch("/config", response_model=OwnerConfigResponse)
async def owner_update_config(
    data: OwnerConfigUpdate,
    db: AsyncSession = Depends(get_db),
    owner: User = Depends(get_owner_user),
):
    """Update platform configuration (owner only)."""
    config = await _get_or_create_config(db)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)

    return OwnerConfigResponse(
        checkout_type=config.checkout_type,
        product_source=config.product_source,
        promo_enabled=config.promo_enabled,
        mailing_enabled=config.mailing_enabled,
        delivery_enabled=config.delivery_enabled,
        pickup_enabled=config.pickup_enabled,
        delivery_sdek_enabled=config.delivery_sdek_enabled,
        delivery_pochta_enabled=config.delivery_pochta_enabled,
        delivery_yandex_enabled=config.delivery_yandex_enabled,
        moysklad_token=_mask_secret(config.moysklad_token),
        one_c_endpoint=config.one_c_endpoint,
        one_c_login=config.one_c_login,
        one_c_password=_mask_secret(config.one_c_password),
        payment_provider_token=_mask_secret(config.payment_provider_token),
        yandex_maps_key=_mask_secret(config.yandex_maps_key),
        support_link=config.support_link,
        sync_interval_minutes=config.sync_interval_minutes,
    )





