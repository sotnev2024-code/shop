from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.cart import CartItem
from app.db.models.product import Product
from app.db.models.product_variant import ProductVariant
from app.db.models.modification_type import ModificationType
from app.db.models.user import User
from app.api.deps import get_current_user
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse, CartItemResponse
from app.api.v1.products import _build_media_list, _build_variant_data

router = APIRouter()


def _variant_key(modification_type_id: int | None, modification_value: str | None) -> str:
    if modification_type_id is None and (modification_value is None or modification_value == ""):
        return ""
    return f"{modification_type_id or ''}:{modification_value or ''}"


def _category_to_response(category) -> dict:
    """Build CategoryResponse dict without touching category.children (avoids lazy load)."""
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "sort_order": category.sort_order,
        "is_active": category.is_active,
        "parent_id": getattr(category, "parent_id", None),
        "children": [],
    }


def _product_to_response_dict(product: Product) -> dict:
    """Build dict for ProductResponse inside CartItemResponse (no ORM variants)."""
    mod_type, variants_short = _build_variant_data(product)
    cats = getattr(product, "categories", None) or []
    first_cat = cats[0] if cats else None
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "old_price": getattr(product, "old_price", None),
        "image_url": product.image_url,
        "is_available": product.is_available,
        "stock_quantity": product.stock_quantity,
        "category_ids": [c.id for c in cats],
        "external_id": getattr(product, "external_id", None),
        "created_at": product.created_at,
        "category_id": first_cat.id if first_cat else None,
        "category": _category_to_response(first_cat) if first_cat else None,
        "categories": [_category_to_response(c) for c in cats],
        "is_favorite": False,
        "media": _build_media_list(product),
        "modification_type": mod_type,
        "variants": variants_short,
    }


def _cart_item_to_response(item: CartItem) -> CartItemResponse:
    data = {
        "id": item.id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "product": _product_to_response_dict(item.product),
        "modification_type_id": item.modification_type_id,
        "modification_value": item.modification_value,
        "modification_label": None,
    }
    resp = CartItemResponse.model_validate(data)
    if item.modification_type_id and item.modification_value and getattr(item, "modification_type", None):
        resp.modification_label = f"{item.modification_type.name}: {item.modification_value}"
    return resp


@router.get("/cart", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get user's cart."""
    result = await db.execute(
        select(CartItem)
        .where(CartItem.user_id == user.id)
        .options(
            selectinload(CartItem.product).selectinload(Product.categories),
            selectinload(CartItem.product).selectinload(Product.media),
            selectinload(CartItem.product).selectinload(Product.variants).selectinload(ProductVariant.modification_type),
            selectinload(CartItem.modification_type),
        )
    )
    items = result.scalars().all()

    total_price = sum(item.product.price * item.quantity for item in items)
    total_items = sum(item.quantity for item in items)

    return CartResponse(
        items=[_cart_item_to_response(item) for item in items],
        total_price=float(total_price),
        total_items=total_items,
    )


@router.post("/cart", response_model=CartItemResponse)
async def add_to_cart(
    data: CartItemAdd,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add product to cart or update quantity. For products with variants, pass modification_type_id and modification_value."""
    result = await db.execute(
        select(Product)
        .where(Product.id == data.product_id)
        .options(selectinload(Product.variants))
    )
    product = result.scalar_one_or_none()
    if not product or not product.is_available:
        raise HTTPException(status_code=404, detail="Product not found")

    variant_key = _variant_key(data.modification_type_id, data.modification_value)
    has_variants = bool(product.variants)

    if has_variants:
        if not data.modification_type_id or not data.modification_value:
            raise HTTPException(status_code=400, detail="Выберите вариант товара (например размер)")
        var_result = await db.execute(
            select(ProductVariant).where(
                ProductVariant.product_id == product.id,
                ProductVariant.modification_type_id == data.modification_type_id,
                ProductVariant.value == data.modification_value,
            )
        )
        variant = var_result.scalar_one_or_none()
        if not variant:
            raise HTTPException(status_code=400, detail="Такого варианта нет у товара")
        if variant.quantity <= 0:
            raise HTTPException(status_code=400, detail="Этого варианта нет в наличии")
        max_stock = variant.quantity
    else:
        if data.modification_type_id or data.modification_value:
            raise HTTPException(status_code=400, detail="У этого товара нет вариантов")
        if product.stock_quantity <= 0:
            raise HTTPException(status_code=400, detail="Товар закончился на складе")
        max_stock = product.stock_quantity

    result = await db.execute(
        select(CartItem).where(
            CartItem.user_id == user.id,
            CartItem.product_id == data.product_id,
            CartItem.variant_key == variant_key,
        )
    )
    cart_item = result.scalar_one_or_none()

    if cart_item:
        new_qty = min(cart_item.quantity + data.quantity, max_stock)
        cart_item.quantity = new_qty
    else:
        qty = min(data.quantity, max_stock)
        cart_item = CartItem(
            user_id=user.id,
            product_id=data.product_id,
            quantity=qty,
            modification_type_id=data.modification_type_id,
            modification_value=data.modification_value,
            variant_key=variant_key,
        )
        db.add(cart_item)

    await db.commit()
    await db.refresh(cart_item)

    result = await db.execute(
        select(CartItem)
        .where(CartItem.id == cart_item.id)
        .options(
            selectinload(CartItem.product).selectinload(Product.categories),
            selectinload(CartItem.product).selectinload(Product.media),
            selectinload(CartItem.product).selectinload(Product.variants).selectinload(ProductVariant.modification_type),
            selectinload(CartItem.modification_type),
        )
    )
    cart_item = result.scalar_one()
    return _cart_item_to_response(cart_item)


@router.patch("/cart/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update cart item quantity. Set 0 to remove."""
    result = await db.execute(
        select(CartItem)
        .where(CartItem.id == item_id, CartItem.user_id == user.id)
        .options(
            selectinload(CartItem.product).selectinload(Product.categories),
            selectinload(CartItem.product).selectinload(Product.media),
            selectinload(CartItem.product).selectinload(Product.variants).selectinload(ProductVariant.modification_type),
            selectinload(CartItem.modification_type),
        )
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if data.quantity == 0:
        resp = _cart_item_to_response(cart_item)
        await db.delete(cart_item)
        await db.commit()
        return resp

    product = cart_item.product
    if cart_item.modification_type_id and cart_item.modification_value:
        var_result = await db.execute(
            select(ProductVariant).where(
                ProductVariant.product_id == product.id,
                ProductVariant.modification_type_id == cart_item.modification_type_id,
                ProductVariant.value == cart_item.modification_value,
            )
        )
        variant = var_result.scalar_one_or_none()
        max_stock = variant.quantity if variant else 0
    else:
        max_stock = product.stock_quantity

    if max_stock <= 0:
        await db.delete(cart_item)
        await db.commit()
        raise HTTPException(status_code=400, detail="Товар закончился на складе")

    qty = min(data.quantity, max_stock)
    cart_item.quantity = qty
    await db.commit()
    await db.refresh(cart_item)
    result = await db.execute(
        select(CartItem)
        .where(CartItem.id == cart_item.id)
        .options(
            selectinload(CartItem.product).selectinload(Product.categories),
            selectinload(CartItem.product).selectinload(Product.media),
            selectinload(CartItem.product).selectinload(Product.variants).selectinload(ProductVariant.modification_type),
            selectinload(CartItem.modification_type),
        )
    )
    return _cart_item_to_response(result.scalar_one())


@router.delete("/cart/{item_id}")
async def remove_from_cart(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove item from cart."""
    result = await db.execute(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id)
    )
    cart_item = result.scalar_one_or_none()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    await db.delete(cart_item)
    await db.commit()
    return {"ok": True}


@router.delete("/cart")
async def clear_cart(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Clear entire cart."""
    await db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    await db.commit()
    return {"ok": True}


@router.post("/cart/validate")
async def validate_cart(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Validate all cart items against current stock.
    Removes out-of-stock items, adjusts over-stock quantities.
    Returns what changed so the frontend can notify the user.
    """
    result = await db.execute(
        select(CartItem)
        .where(CartItem.user_id == user.id)
        .options(
            selectinload(CartItem.product).selectinload(Product.categories),
            selectinload(CartItem.product).selectinload(Product.media),
            selectinload(CartItem.product).selectinload(Product.variants).selectinload(ProductVariant.modification_type),
            selectinload(CartItem.modification_type),
        )
    )
    cart_items = result.scalars().all()

    removed: list[dict] = []
    adjusted: list[dict] = []

    for item in cart_items:
        product = item.product
        if not product or not product.is_available:
            removed.append({
                "product_id": item.product_id,
                "product_name": product.name if product else "Удалённый товар",
                "old_quantity": item.quantity,
            })
            await db.delete(item)
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
            await db.delete(item)
            continue

        if item.quantity > max_stock:
            adjusted.append({
                "product_id": item.product_id,
                "product_name": product.name,
                "old_quantity": item.quantity,
                "new_quantity": max_stock,
            })
            item.quantity = max_stock

    await db.commit()

    result = await db.execute(
        select(CartItem)
        .where(CartItem.user_id == user.id)
        .options(
            selectinload(CartItem.product).selectinload(Product.categories),
            selectinload(CartItem.product).selectinload(Product.media),
            selectinload(CartItem.product).selectinload(Product.variants).selectinload(ProductVariant.modification_type),
            selectinload(CartItem.modification_type),
        )
    )
    remaining_items = result.scalars().all()

    total_price = sum(float(i.product.price) * i.quantity for i in remaining_items)
    total_items = sum(i.quantity for i in remaining_items)

    return {
        "items": [_cart_item_to_response(i) for i in remaining_items],
        "total_price": total_price,
        "total_items": total_items,
        "removed": removed,
        "adjusted": adjusted,
    }
