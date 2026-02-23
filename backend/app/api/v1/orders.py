from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.cart import CartItem
from app.db.models.order import Order, OrderItem
from app.db.models.product import Product
from app.db.models.product_variant import ProductVariant
from app.db.models.promo import PromoCode
from app.db.models.user import User
from app.db.models.app_config import AppConfig
from app.db.models.bonus_transaction import BonusTransaction
from app.api.deps import get_current_user
from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderItemResponse
from app.bot.handlers.admin_notify import notify_new_order

router = APIRouter()


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new order from cart items."""
    result = await db.execute(
        select(CartItem)
        .where(CartItem.user_id == user.id)
        .options(
            selectinload(CartItem.product),
            selectinload(CartItem.product).selectinload(Product.variants),
            selectinload(CartItem.modification_type),
        )
    )
    cart_items = list(result.scalars().all())

    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    removed: list[dict] = []
    adjusted: list[dict] = []

    for item in cart_items:
        product = item.product
        await db.refresh(product)
        if not product.is_available:
            removed.append({
                "product_id": item.product_id,
                "product_name": product.name,
                "old_quantity": item.quantity,
            })
            continue
        if item.modification_type_id and item.modification_value:
            var_result = await db.execute(
                select(ProductVariant).where(
                    ProductVariant.product_id == product.id,
                    ProductVariant.modification_type_id == item.modification_type_id,
                    ProductVariant.value == item.modification_value,
                )
            )
            variant = var_result.scalar_one_or_none()
            max_stock = variant.quantity if variant else 0
        else:
            max_stock = product.stock_quantity
        if max_stock <= 0:
            removed.append({
                "product_id": item.product_id,
                "product_name": product.name,
                "old_quantity": item.quantity,
            })
        elif item.quantity > max_stock:
            adjusted.append({
                "product_id": item.product_id,
                "product_name": product.name,
                "old_quantity": item.quantity,
                "new_quantity": max_stock,
            })

    if removed or adjusted:
        for info in removed:
            for item in cart_items[:]:
                if (
                    item.product_id == info["product_id"]
                    and item.quantity == info["old_quantity"]
                ):
                    await db.delete(item)
                    cart_items.remove(item)
                    break
        for info in adjusted:
            for item in cart_items:
                if (
                    item.product_id == info["product_id"]
                    and item.quantity == info["old_quantity"]
                ):
                    item.quantity = info["new_quantity"]
                    break
        await db.commit()
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Некоторые товары изменились",
                "removed": removed,
                "adjusted": adjusted,
            },
        )

    # ── Calculate total ───────────────────────────────────────────────
    total = sum(item.product.price * item.quantity for item in cart_items)
    discount = 0.0
    promo_code_id = None
    free_delivery_promo = False

    # Apply promo code
    if data.promo_code:
        promo_result = await db.execute(
            select(PromoCode).where(
                PromoCode.code == data.promo_code,
                PromoCode.is_active == True,
            )
        )
        promo = promo_result.scalar_one_or_none()
        if promo:
            now = datetime.now(tz=None)
            valid = True
            if promo.valid_from and now < promo.valid_from.replace(tzinfo=None):
                valid = False
            if promo.valid_until and now > promo.valid_until.replace(tzinfo=None):
                valid = False
            if promo.max_uses and promo.used_count >= promo.max_uses:
                valid = False
            if float(total) < float(promo.min_order_amount):
                valid = False

            if valid:
                used_by_user = await db.execute(
                    select(func.count()).select_from(Order).where(
                        Order.user_id == user.id,
                        Order.promo_code_id == promo.id,
                    )
                )
                if (used_by_user.scalar() or 0) > 0:
                    raise HTTPException(
                        status_code=400,
                        detail="Вы уже использовали этот промокод",
                    )
                if getattr(promo, "first_order_only", False):
                    user_orders_count = await db.execute(
                        select(func.count()).select_from(Order).where(Order.user_id == user.id)
                    )
                    if (user_orders_count.scalar() or 0) > 0:
                        raise HTTPException(
                            status_code=400,
                            detail="Промокод действует только на первый заказ",
                        )

                if promo.discount_type == "free_delivery":
                    if not data.delivery_type or data.delivery_type == "pickup":
                        raise HTTPException(
                            status_code=400,
                            detail="Промокод на бесплатную доставку не действует при самовывозе",
                        )
                    config_result = await db.execute(select(AppConfig).limit(1))
                    app_config = config_result.scalar_one_or_none()
                    if app_config:
                        min_free = float(getattr(app_config, "free_delivery_min_amount", 0) or 0)
                        if min_free > 0 and float(total) >= min_free:
                            raise HTTPException(
                                status_code=400,
                                detail="Доставка уже бесплатная, промокод не применён",
                            )
                    free_delivery_promo = True
                    discount = 0.0
                    promo_code_id = promo.id
                    promo.used_count += 1
                else:
                    if promo.discount_type == "percent":
                        discount = float(total) * float(promo.discount_value) / 100
                    else:
                        discount = float(promo.discount_value)
                    discount = min(discount, float(total))
                    promo_code_id = promo.id
                    promo.used_count += 1

    total_after_promo = float(total) - discount
    bonus_used = 0.0
    if data.bonus_to_use and float(data.bonus_to_use) > 0:
        config_result = await db.execute(select(AppConfig).limit(1))
        app_config = config_result.scalar_one_or_none()
        await db.refresh(user)
        if app_config and getattr(app_config, "bonus_enabled", False) and getattr(app_config, "bonus_spend_enabled", False):
            limit_type = getattr(app_config, "bonus_spend_limit_type", "percent")
            limit_value = float(getattr(app_config, "bonus_spend_limit_value", 0))
            if limit_type == "percent":
                max_allowed = total_after_promo * limit_value / 100 if limit_value else 0
            else:
                max_allowed = limit_value
            balance = float(user.bonus_balance or 0)
            bonus_used = min(float(data.bonus_to_use), balance, max_allowed)
            bonus_used = round(max(0, bonus_used), 0)  # только целые баллы

    subtotal = total_after_promo - bonus_used
    delivery_fee = 0.0
    if data.delivery_type and data.delivery_type != "pickup":
        if free_delivery_promo:
            delivery_fee = 0.0
        else:
            config_result = await db.execute(select(AppConfig).limit(1))
            app_config = config_result.scalar_one_or_none()
            if app_config:
                cost = float(getattr(app_config, "delivery_cost", 0) or 0)
                min_free = float(getattr(app_config, "free_delivery_min_amount", 0) or 0)
                if min_free > 0 and subtotal >= min_free:
                    delivery_fee = 0.0
                else:
                    delivery_fee = cost

    # ── Create order ──────────────────────────────────────────────────
    order = Order(
        user_id=user.id,
        status="new",
        total=subtotal + delivery_fee,
        discount=discount,
        bonus_used=bonus_used,
        delivery_fee=delivery_fee,
        delivery_type=data.delivery_type,
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        address=data.address,
        address_coords=data.address_coords,
        delivery_service=data.delivery_service,
        promo_code_id=promo_code_id,
    )
    db.add(order)
    await db.flush()

    if bonus_used > 0:
        user.bonus_balance = float(user.bonus_balance or 0) - bonus_used
        tx = BonusTransaction(user_id=user.id, amount=-bonus_used, kind="spend", order_id=order.id)
        db.add(tx)

    items_text_parts = []
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price_at_order=float(cart_item.product.price),
            modification_type_id=cart_item.modification_type_id,
            modification_value=cart_item.modification_value,
        )
        db.add(order_item)
        label = (
            f" ({cart_item.modification_type.name}: {cart_item.modification_value})"
            if cart_item.modification_type_id and cart_item.modification_value
            and getattr(cart_item, "modification_type", None)
            else ""
        )
        items_text_parts.append(
            f"  • {cart_item.product.name}{label} x{cart_item.quantity} — "
            f"{float(cart_item.product.price) * cart_item.quantity:.2f} ₽"
        )

        if cart_item.modification_type_id and cart_item.modification_value:
            var_result = await db.execute(
                select(ProductVariant).where(
                    ProductVariant.product_id == cart_item.product_id,
                    ProductVariant.modification_type_id == cart_item.modification_type_id,
                    ProductVariant.value == cart_item.modification_value,
                )
            )
            variant = var_result.scalar_one_or_none()
            if variant:
                variant.quantity = max(0, variant.quantity - cart_item.quantity)
        else:
            cart_item.product.stock_quantity = max(
                0, cart_item.product.stock_quantity - cart_item.quantity
            )
            if cart_item.product.stock_quantity <= 0:
                cart_item.product.is_available = False

    # Clear cart
    await db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    await db.commit()
    await db.refresh(order)

    # Notify admin
    try:
        await notify_new_order(
            order_id=order.id,
            customer_name=data.customer_name,
            customer_phone=data.customer_phone,
            address=data.address,
            delivery_type=data.delivery_type,
            total=float(order.total),
            items_text="\n".join(items_text_parts),
            bonus_used=float(order.bonus_used or 0),
        )
    except Exception:
        pass  # Don't fail order if notification fails

    result = await db.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.modification_type),
        )
    )
    order = result.scalar_one()

    return _order_to_response(order)


@router.get("/orders", response_model=OrderListResponse)
async def get_orders(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get user's orders."""
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user.id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.modification_type),
        )
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    return OrderListResponse(
        items=[_order_to_response(o) for o in orders],
        total=len(orders),
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single order."""
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user.id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.modification_type),
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_response(order)


def _order_to_response(order: Order) -> OrderResponse:
    items = []
    for item in order.items:
        modification_label = None
        if item.modification_type_id and item.modification_value and getattr(item, "modification_type", None):
            modification_label = f"{item.modification_type.name}: {item.modification_value}"
        elif item.modification_value:
            modification_label = item.modification_value
        items.append(
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_order=float(item.price_at_order),
                product_name=item.product.name if item.product else "",
                modification_type_id=item.modification_type_id,
                modification_value=item.modification_value,
                modification_label=modification_label,
            )
        )
    return OrderResponse(
        id=order.id,
        status=order.status,
        total=float(order.total),
        discount=float(order.discount),
        bonus_used=float(order.bonus_used or 0),
        delivery_fee=float(order.delivery_fee or 0),
        delivery_type=order.delivery_type,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        address=order.address,
        payment_status=order.payment_status,
        delivery_service=order.delivery_service,
        tracking_number=order.tracking_number,
        created_at=order.created_at,
        items=items,
    )
