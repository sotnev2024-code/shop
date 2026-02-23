from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models.promo import PromoCode
from app.db.models.order import Order
from app.db.models.app_config import AppConfig
from app.api.deps import get_current_user
from app.schemas.promo import PromoCodeCheck, PromoCodeCheckResponse

router = APIRouter()


@router.post("/promo/check", response_model=PromoCodeCheckResponse)
async def check_promo_code(
    data: PromoCodeCheck,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    """Validate a promo code (with user: one use per user, first order only; optional cart/delivery for free_delivery)."""
    if not settings.promo_enabled:
        return PromoCodeCheckResponse(valid=False, message="Промокоды отключены")

    result = await db.execute(
        select(PromoCode).where(
            PromoCode.code == data.code,
            PromoCode.is_active == True,
        )
    )
    promo = result.scalar_one_or_none()

    if not promo:
        return PromoCodeCheckResponse(valid=False, message="Промокод не найден")

    now = datetime.now(tz=None)
    if promo.valid_from and now < promo.valid_from.replace(tzinfo=None):
        return PromoCodeCheckResponse(valid=False, message="Промокод ещё не активен")
    if promo.valid_until and now > promo.valid_until.replace(tzinfo=None):
        return PromoCodeCheckResponse(valid=False, message="Промокод истёк")
    if promo.max_uses and promo.used_count >= promo.max_uses:
        return PromoCodeCheckResponse(valid=False, message="Промокод использован максимальное число раз")

    used_by_user = await db.execute(
        select(func.count()).select_from(Order).where(
            Order.user_id == user.id,
            Order.promo_code_id == promo.id,
        )
    )
    if (used_by_user.scalar() or 0) > 0:
        return PromoCodeCheckResponse(valid=False, message="Вы уже использовали этот промокод")

    if getattr(promo, "first_order_only", False):
        user_orders_count = await db.execute(
            select(func.count()).select_from(Order).where(Order.user_id == user.id)
        )
        if (user_orders_count.scalar() or 0) > 0:
            return PromoCodeCheckResponse(valid=False, message="Промокод действует только на первый заказ")

    if promo.discount_type == "free_delivery":
        if data.delivery_type == "pickup" or not data.delivery_type:
            return PromoCodeCheckResponse(valid=False, message="Промокод на бесплатную доставку не действует при самовывозе")
        if data.cart_total is not None:
            config_result = await db.execute(select(AppConfig).limit(1))
            app_config = config_result.scalar_one_or_none()
            if app_config:
                min_free = float(getattr(app_config, "free_delivery_min_amount", 0) or 0)
                if min_free > 0 and data.cart_total >= min_free:
                    return PromoCodeCheckResponse(valid=False, message="Доставка уже бесплатная, промокод не применён")
        return PromoCodeCheckResponse(
            valid=True,
            discount_type="free_delivery",
            discount_value=0,
            message="Бесплатная доставка",
        )

    return PromoCodeCheckResponse(
        valid=True,
        discount_type=promo.discount_type,
        discount_value=float(promo.discount_value),
        message=f"Скидка {'%' if promo.discount_type == 'percent' else '₽'}: {float(promo.discount_value)}",
    )





