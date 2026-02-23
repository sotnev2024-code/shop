import logging
import os
import uuid
import shutil
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.config import settings, ProductSource
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.order import Order, OrderItem
from app.db.models.product import Product
from app.db.models.product_media import ProductMedia
from app.db.models.product_variant import ProductVariant
from app.db.models.modification_type import ModificationType
from app.db.models.modification_value import ModificationValue
from app.db.models.category import Category
from app.db.models.promo import PromoCode
from app.db.models.banner import Banner
from app.db.models.app_config import AppConfig
from app.db.models.bonus_transaction import BonusTransaction
from app.api.deps import get_admin_user
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    BulkPriceRequest, BulkPriceResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse, ProductMediaResponse,
    ModificationTypeCreate, ModificationTypeUpdate, ModificationTypeResponse,
    ModificationValueCreate, ModificationValueResponse,
    ProductVariantCreate, ProductVariantUpdate, ProductVariantResponse,
    ModificationTypeShort, ProductVariantShort,
)
from app.schemas.order import OrderResponse, OrderListResponse, OrderStatusUpdate
from app.schemas.promo import PromoCodeCreate, PromoCodeResponse
from app.schemas.banner import BannerResponse, BannerCreate, BannerUpdate
from app.bot.bot import get_bot, is_bot_configured
from app.services.product_loader import get_product_loader

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads"

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

router = APIRouter()


# ---- Dashboard / Stats ----

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Get dashboard statistics."""
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)
    week_ago = now - timedelta(days=7)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    new_users_month = (
        await db.execute(
            select(func.count(User.id)).where(User.created_at >= month_ago)
        )
    ).scalar() or 0

    total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    orders_month = (
        await db.execute(
            select(func.count(Order.id)).where(Order.created_at >= month_ago)
        )
    ).scalar() or 0
    orders_week = (
        await db.execute(
            select(func.count(Order.id)).where(Order.created_at >= week_ago)
        )
    ).scalar() or 0

    revenue_total = (
        await db.execute(select(func.sum(Order.total)))
    ).scalar() or 0
    revenue_month = (
        await db.execute(
            select(func.sum(Order.total)).where(Order.created_at >= month_ago)
        )
    ).scalar() or 0

    total_products = (await db.execute(select(func.count(Product.id)))).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "new_month": new_users_month,
        },
        "orders": {
            "total": total_orders,
            "month": orders_month,
            "week": orders_week,
        },
        "revenue": {
            "total": float(revenue_total),
            "month": float(revenue_month),
        },
        "products": {
            "total": total_products,
        },
    }


# ---- Orders management ----

@router.get("/orders", response_model=OrderListResponse)
async def admin_get_orders(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Get all orders (admin)."""
    from sqlalchemy.orm import selectinload

    query = select(Order)
    if status:
        query = query.where(Order.status == status)

    total_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_q)).scalar() or 0

    query = (
        query.options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.modification_type),
        )
        .order_by(Order.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    orders = result.scalars().all()

    from app.api.v1.orders import _order_to_response

    return OrderListResponse(
        items=[_order_to_response(o) for o in orders],
        total=total,
    )


@router.patch("/orders/{order_id}", response_model=OrderResponse)
async def admin_update_order(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update order status (admin)."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.items).selectinload(OrderItem.modification_type),
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    old_status = order.status
    order.status = data.status
    if data.tracking_number:
        order.tracking_number = data.tracking_number

    if old_status != "done" and data.status == "done":
        config_result = await db.execute(select(AppConfig).limit(1))
        app_config = config_result.scalar_one_or_none()
        # Не начисляем бонусы за покупку, если по заказу списывали баллы
        if app_config and getattr(app_config, "bonus_enabled", False) and getattr(app_config, "bonus_purchase_enabled", False) and float(order.bonus_used or 0) == 0:
            percent = float(getattr(app_config, "bonus_purchase_percent", 0))
            if percent > 0:
                order_total = float(order.total) + float(order.bonus_used)
                amount = round(order_total * percent / 100, 2)
                if amount > 0 and order.user:
                    order.user.bonus_balance = float(order.user.bonus_balance or 0) + amount
                    tx = BonusTransaction(user_id=order.user_id, amount=amount, kind="purchase", order_id=order.id)
                    db.add(tx)

    if old_status != "cancelled" and data.status == "cancelled" and float(order.bonus_used or 0) > 0 and order.user:
        refund = float(order.bonus_used)
        order.user.bonus_balance = float(order.user.bonus_balance or 0) + refund
        tx = BonusTransaction(user_id=order.user_id, amount=refund, kind="refund", order_id=order.id)
        db.add(tx)

    # Отмена → выполнен: бонусы ранее вернули при отмене, теперь снова списываем
    if old_status == "cancelled" and data.status == "done" and float(order.bonus_used or 0) > 0 and order.user:
        deduct = float(order.bonus_used)
        order.user.bonus_balance = float(order.user.bonus_balance or 0) - deduct
        tx = BonusTransaction(user_id=order.user_id, amount=-deduct, kind="spend", order_id=order.id)
        db.add(tx)

    await db.commit()
    await db.refresh(order)

    from app.api.v1.orders import _order_to_response
    return _order_to_response(order)


# ---- Product management ----

@router.get("/products", response_model=ProductListResponse)
async def admin_list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    price_equals: Optional[float] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List all products for admin (no availability/stock filter). Optional filters by category, price."""
    query = select(Product)

    if category_id is not None:
        category_ids_cte = (
            select(Category.id).where(Category.id == category_id).cte(recursive=True)
        )
        category_ids_cte = category_ids_cte.union_all(
            select(Category.id).where(Category.parent_id == category_ids_cte.c.id)
        )
        query = query.where(Product.category_id.in_(select(category_ids_cte.c.id)))
    if price_equals is not None:
        query = query.where(Product.price == price_equals)
    if price_min is not None:
        query = query.where(Product.price >= price_min)
    if price_max is not None:
        query = query.where(Product.price <= price_max)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = (
        query.options(
            selectinload(Product.category),
            selectinload(Product.media),
            selectinload(Product.variants).selectinload(ProductVariant.modification_type),
        )
        .order_by(Product.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    products = result.scalars().all()

    items = []
    for p in products:
        mod_type, variants_short = _build_product_variant_data(p)
        items.append(ProductResponse.model_validate(_product_to_response_dict(p, mod_type, variants_short)))

    return ProductListResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("/products/bulk-price", response_model=BulkPriceResponse)
async def admin_bulk_price(
    data: BulkPriceRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Bulk update product prices by scope (all / product_ids / price_equals / price_range / category) and operation (add/subtract amount or percent)."""
    query = select(Product)

    if data.scope == "product_ids":
        if not data.product_ids:
            raise HTTPException(status_code=400, detail="product_ids required when scope is product_ids")
        query = query.where(Product.id.in_(data.product_ids))
    elif data.scope == "price_equals":
        if data.price_equals is None:
            raise HTTPException(status_code=400, detail="price_equals required when scope is price_equals")
        query = query.where(Product.price == data.price_equals)
    elif data.scope == "price_range":
        if data.price_min is not None:
            query = query.where(Product.price >= data.price_min)
        if data.price_max is not None:
            query = query.where(Product.price <= data.price_max)
    elif data.scope == "category":
        if data.category_id is None:
            raise HTTPException(status_code=400, detail="category_id required when scope is category")
        category_ids_cte = (
            select(Category.id).where(Category.id == data.category_id).cte(recursive=True)
        )
        category_ids_cte = category_ids_cte.union_all(
            select(Category.id).where(Category.parent_id == category_ids_cte.c.id)
        )
        query = query.where(Product.category_id.in_(select(category_ids_cte.c.id)))
    # scope "all" -> no extra filters

    result = await db.execute(query)
    products = result.scalars().all()

    def new_price(price: float) -> float:
        if data.operation == "set_to":
            p = data.value
        else:
            p = float(price)
            if data.operation == "add_amount":
                p += data.value
            elif data.operation == "subtract_amount":
                p -= data.value
            elif data.operation == "add_percent":
                p *= 1 + data.value / 100.0
            elif data.operation == "subtract_percent":
                p *= 1 - data.value / 100.0
            else:
                raise HTTPException(status_code=400, detail="Invalid operation")
        if data.round_to_nearest is not None and data.round_to_nearest > 0:
            p = round(p / data.round_to_nearest) * data.round_to_nearest
        return round(p, 2)

    updated_ids = []
    for product in products:
        # Store as Decimal to avoid float representation (e.g. 3090 -> 3089.99)
        p = new_price(product.price)
        product.price = Decimal(f"{p:.2f}")
        updated_ids.append(product.id)
    await db.commit()
    return BulkPriceResponse(updated_count=len(updated_ids), product_ids=updated_ids)


def _build_product_media_list(product: Product) -> list[ProductMediaResponse]:
    if not product.media:
        if product.image_url:
            return [ProductMediaResponse(id=0, media_type="image", url=product.image_url, sort_order=0)]
        return []
    return [
        ProductMediaResponse(id=m.id, media_type=m.media_type, url=m.file_path, sort_order=m.sort_order)
        for m in sorted(product.media, key=lambda x: x.sort_order)
    ]


def _build_product_variant_data(product: Product) -> tuple[ModificationTypeShort | None, list[ProductVariantShort]]:
    if not product.variants:
        return None, []
    mod_type = None
    short_variants: list[ProductVariantShort] = []
    for v in product.variants:
        if mod_type is None and getattr(v, "modification_type", None):
            mod_type = ModificationTypeShort(id=v.modification_type.id, name=v.modification_type.name)
        short_variants.append(ProductVariantShort(value=v.value, quantity=v.quantity))
    return mod_type, short_variants


def _product_to_response_dict(product: Product, mod_type: ModificationTypeShort | None, variants_short: list[ProductVariantShort]) -> dict:
    """Build dict for ProductResponse.model_validate (avoids ORM variants/media in Pydantic)."""
    price_val = product.price
    old_price_val = getattr(product, "old_price", None)
    # Format via string to avoid Decimal->float precision loss (e.g. 3090 becoming 3089.99...)
    def _norm_price(v):
        if v is None:
            return None
        return float(format(v, ".2f"))
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": _norm_price(price_val),
        "old_price": _norm_price(old_price_val),
        "image_url": product.image_url,
        "is_available": product.is_available,
        "stock_quantity": product.stock_quantity,
        "category_id": product.category_id,
        "external_id": getattr(product, "external_id", None),
        "created_at": product.created_at,
        "category": (
            {
                "id": product.category.id,
                "name": product.category.name,
                "slug": product.category.slug,
                "sort_order": product.category.sort_order,
                "is_active": product.category.is_active,
                "parent_id": getattr(product.category, "parent_id", None),
                "children": [],
            }
            if product.category
            else None
        ),
        "is_favorite": False,
        "media": _build_product_media_list(product),
        "modification_type": mod_type,
        "variants": variants_short,
    }


@router.post("/products", response_model=ProductResponse)
async def admin_create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Create a new product."""
    dump = data.model_dump()
    dump["price"] = Decimal(format(round(float(dump["price"]), 2), ".2f"))
    if dump.get("old_price") is not None:
        dump["old_price"] = Decimal(format(round(float(dump["old_price"]), 2), ".2f"))
    product = Product(**dump)
    db.add(product)
    await db.commit()

    result = await db.execute(
        select(Product)
        .where(Product.id == product.id)
        .options(
            selectinload(Product.category),
            selectinload(Product.media),
            selectinload(Product.variants).selectinload(ProductVariant.modification_type),
        )
    )
    product = result.scalar_one()
    mod_type, variants_short = _build_product_variant_data(product)
    return ProductResponse.model_validate(_product_to_response_dict(product, mod_type, variants_short))


@router.patch("/products/{product_id}", response_model=ProductResponse)
async def admin_update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update a product."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = data.model_dump(exclude_unset=True)
    # Normalize price via string to avoid float precision issues (e.g. 3090 sent as 3089.999...)
    if "price" in update_data and update_data["price"] is not None:
        p = float(update_data["price"])
        update_data["price"] = Decimal(format(round(p, 2), ".2f"))
    if "old_price" in update_data and update_data["old_price"] is not None:
        p = float(update_data["old_price"])
        update_data["old_price"] = Decimal(format(round(p, 2), ".2f"))
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.commit()

    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.category),
            selectinload(Product.media),
            selectinload(Product.variants).selectinload(ProductVariant.modification_type),
        )
    )
    product = result.scalar_one()
    mod_type, variants_short = _build_product_variant_data(product)
    return ProductResponse.model_validate(_product_to_response_dict(product, mod_type, variants_short))


@router.delete("/products/{product_id}")
async def admin_delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Delete a product."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    await db.commit()
    return {"ok": True}


# ---- Product media management ----

@router.post("/products/{product_id}/media", response_model=ProductMediaResponse)
async def admin_upload_media(
    product_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Upload an image or video for a product."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    content_type = file.content_type or ""
    if content_type in ALLOWED_IMAGE_TYPES:
        media_type = "image"
    elif content_type in ALLOWED_VIDEO_TYPES:
        media_type = "video"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: jpg, png, webp, gif, mp4, webm.",
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 50 MB.")

    # Determine extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if not ext:
        ext = ".jpg" if media_type == "image" else ".mp4"

    # Save file
    product_dir = UPLOADS_DIR / "products" / str(product_id)
    product_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = product_dir / filename

    with open(file_path, "wb") as f:
        f.write(content)

    # Determine sort order: videos get -1000 so they sort before images
    existing_count = (
        await db.execute(
            select(func.count(ProductMedia.id)).where(ProductMedia.product_id == product_id)
        )
    ).scalar() or 0

    sort_order = -1000 + existing_count if media_type == "video" else existing_count

    # Create DB record
    relative_path = f"/uploads/products/{product_id}/{filename}"
    media = ProductMedia(
        product_id=product_id,
        media_type=media_type,
        file_path=relative_path,
        sort_order=sort_order,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)

    return ProductMediaResponse(
        id=media.id,
        media_type=media.media_type,
        url=media.file_path,
        sort_order=media.sort_order,
    )


@router.delete("/products/{product_id}/media/{media_id}")
async def admin_delete_media(
    product_id: int,
    media_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Delete a media file from a product."""
    result = await db.execute(
        select(ProductMedia).where(
            ProductMedia.id == media_id,
            ProductMedia.product_id == product_id,
        )
    )
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    # Delete file from disk
    file_full_path = UPLOADS_DIR.parent / media.file_path.lstrip("/")
    if file_full_path.exists():
        file_full_path.unlink()

    await db.delete(media)
    await db.commit()
    return {"ok": True}


@router.patch("/products/{product_id}/media/{media_id}", response_model=ProductMediaResponse)
async def admin_reorder_media(
    product_id: int,
    media_id: int,
    sort_order: int = Query(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update sort order of a media item."""
    result = await db.execute(
        select(ProductMedia).where(
            ProductMedia.id == media_id,
            ProductMedia.product_id == product_id,
        )
    )
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    media.sort_order = sort_order
    await db.commit()
    await db.refresh(media)

    return ProductMediaResponse(
        id=media.id,
        media_type=media.media_type,
        url=media.file_path,
        sort_order=media.sort_order,
    )


# ---- Category management ----

@router.post("/categories/upload")
async def admin_upload_category_image(
    file: UploadFile = File(...),
    admin: User = Depends(get_admin_user),
):
    """Upload an image for a category. Returns { url: "/uploads/categories/..." }."""
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: jpg, png, webp, gif.",
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 50 MB.")
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    category_dir = UPLOADS_DIR / "categories"
    category_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = category_dir / filename
    with open(file_path, "wb") as f:
        f.write(content)
    url = f"/uploads/categories/{filename}"
    return {"url": url}


ALL_CATEGORY_SLUG = "all"


@router.get("/categories", response_model=list[CategoryResponse])
async def admin_list_categories(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List all categories (including empty ones) for admin. Flat list with parent_id; frontend builds tree."""
    result = await db.execute(
        select(Category).where(Category.slug == ALL_CATEGORY_SLUG)
    )
    if result.scalar_one_or_none() is None:
        all_cat = Category(name="Все", slug=ALL_CATEGORY_SLUG, sort_order=0, is_active=True, parent_id=None)
        db.add(all_cat)
        await db.commit()
    result = await db.execute(
        select(Category).order_by(Category.sort_order, Category.name)
    )
    categories = result.scalars().all()
    # Категория «Все» (slug all) только одна — убираем дубликаты по slug на случай старых данных
    seen_all = False
    out = []
    for c in categories:
        if c.slug == ALL_CATEGORY_SLUG:
            if seen_all:
                continue
            seen_all = True
        out.append(
            CategoryResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                sort_order=c.sort_order,
                is_active=c.is_active,
                parent_id=c.parent_id,
                image_url=getattr(c, "image_url", None),
                children=[],
            )
        )
    return out


@router.post("/categories", response_model=CategoryResponse)
async def admin_create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Create a new category."""
    if not data.slug or not data.slug.strip():
        raise HTTPException(status_code=400, detail="Slug не может быть пустым")
    if data.slug.strip().lower() == ALL_CATEGORY_SLUG:
        raise HTTPException(status_code=400, detail="Категорию «Все» нельзя создать вручную")
    if data.parent_id is not None:
        parent = await db.get(Category, data.parent_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Родительская категория не найдена")
    try:
        category = Category(**data.model_dump())
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return CategoryResponse.model_validate({
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "sort_order": category.sort_order,
            "is_active": category.is_active,
            "parent_id": category.parent_id,
            "image_url": category.image_url,
            "children": [],
        })
    except IntegrityError as e:
        await db.rollback()
        error_str = str(e).lower()
        if "unique constraint" in error_str or "unique constraint failed" in error_str:
            raise HTTPException(status_code=400, detail=f"Категория с slug '{data.slug}' уже существует")
        logger.error(f"IntegrityError creating category: {e}")
        raise HTTPException(status_code=400, detail="Ошибка создания категории: нарушение ограничений базы данных")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка создания категории: {str(e)}")


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
async def admin_update_category(
    category_id: int,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update a category."""
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = data.model_dump(exclude_unset=True)
    if getattr(category, "slug", None) == ALL_CATEGORY_SLUG:
        # Категория «Все»: только картинка (и is_active), не меняем имя, slug, родителя, порядок
        update_data.pop("sort_order", None)
        update_data.pop("parent_id", None)
        update_data.pop("name", None)
        update_data.pop("slug", None)
    if "parent_id" in update_data and update_data["parent_id"] == category_id:
        raise HTTPException(status_code=400, detail="Категория не может быть родителем самой себя")
    for key, value in update_data.items():
        setattr(category, key, value)

    await db.commit()
    await db.refresh(category)
    return CategoryResponse.model_validate({
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "sort_order": category.sort_order,
        "is_active": category.is_active,
        "parent_id": category.parent_id,
        "image_url": category.image_url,
        "children": [],
    })


@router.delete("/categories/{category_id}")
async def admin_delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Delete a category."""
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if getattr(category, "slug", None) == ALL_CATEGORY_SLUG:
        raise HTTPException(status_code=400, detail="Нельзя удалить категорию «Все»")
    await db.delete(category)
    await db.commit()
    return {"ok": True}


# ---- Modification types ----

@router.get("/modification-types", response_model=list[ModificationTypeResponse])
async def admin_list_modification_types(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List all modification types with their predefined values."""
    result = await db.execute(
        select(ModificationType)
        .order_by(ModificationType.sort_order, ModificationType.name)
        .options(selectinload(ModificationType.values))
    )
    return result.scalars().all()


@router.post("/modification-types", response_model=ModificationTypeResponse)
async def admin_create_modification_type(
    data: ModificationTypeCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Create a modification type and optionally its predefined values."""
    payload = data.model_dump()
    values_list = payload.pop("values", [])
    mt = ModificationType(**payload)
    db.add(mt)
    await db.flush()
    for i, val in enumerate(values_list):
        if val and str(val).strip():
            db.add(ModificationValue(
                modification_type_id=mt.id,
                value=str(val).strip(),
                sort_order=i,
            ))
    await db.commit()
    await db.refresh(mt)
    result = await db.execute(
        select(ModificationType)
        .where(ModificationType.id == mt.id)
        .options(selectinload(ModificationType.values))
    )
    return ModificationTypeResponse.model_validate(result.scalar_one())


@router.patch("/modification-types/{type_id}", response_model=ModificationTypeResponse)
async def admin_update_modification_type(
    type_id: int,
    data: ModificationTypeUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update a modification type."""
    result = await db.execute(
        select(ModificationType).where(ModificationType.id == type_id).options(selectinload(ModificationType.values))
    )
    mt = result.scalar_one_or_none()
    if not mt:
        raise HTTPException(status_code=404, detail="Modification type not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(mt, key, value)
    await db.commit()
    await db.refresh(mt)
    result = await db.execute(
        select(ModificationType).where(ModificationType.id == type_id).options(selectinload(ModificationType.values))
    )
    return ModificationTypeResponse.model_validate(result.scalar_one())


@router.delete("/modification-types/{type_id}")
async def admin_delete_modification_type(
    type_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Delete a modification type if not used by any product variant."""
    mt = await db.get(ModificationType, type_id)
    if not mt:
        raise HTTPException(status_code=404, detail="Modification type not found")
    result = await db.execute(
        select(ProductVariant.id).where(ProductVariant.modification_type_id == type_id).limit(1)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Тип модификации используется в товарах, удаление невозможно",
        )
    await db.delete(mt)
    await db.commit()
    return {"ok": True}


@router.get("/modification-types/{type_id}/values", response_model=list[ModificationValueResponse])
async def admin_list_modification_type_values(
    type_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List predefined values for a modification type."""
    mt = await db.get(ModificationType, type_id)
    if not mt:
        raise HTTPException(status_code=404, detail="Modification type not found")
    result = await db.execute(
        select(ModificationValue).where(ModificationValue.modification_type_id == type_id).order_by(ModificationValue.sort_order)
    )
    return result.scalars().all()


@router.post("/modification-types/{type_id}/values", response_model=ModificationValueResponse)
async def admin_add_modification_type_value(
    type_id: int,
    data: ModificationValueCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Add a predefined value to a modification type."""
    mt = await db.get(ModificationType, type_id)
    if not mt:
        raise HTTPException(status_code=404, detail="Modification type not found")
    result = await db.execute(
        select(ModificationValue).where(
            ModificationValue.modification_type_id == type_id,
            ModificationValue.value == data.value,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Такое значение уже есть")
    mv = ModificationValue(modification_type_id=type_id, value=data.value.strip(), sort_order=data.sort_order)
    db.add(mv)
    await db.commit()
    await db.refresh(mv)
    return ModificationValueResponse.model_validate(mv)


@router.delete("/modification-types/{type_id}/values/{value_id}")
async def admin_delete_modification_type_value(
    type_id: int,
    value_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Remove a predefined value from a modification type."""
    result = await db.execute(
        select(ModificationValue).where(
            ModificationValue.id == value_id,
            ModificationValue.modification_type_id == type_id,
        )
    )
    mv = result.scalar_one_or_none()
    if not mv:
        raise HTTPException(status_code=404, detail="Value not found")
    await db.delete(mv)
    await db.commit()
    return {"ok": True}


# ---- Product variants ----

@router.get("/products/{product_id}/variants", response_model=list[ProductVariantResponse])
async def admin_list_product_variants(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List variants for a product."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    result = await db.execute(
        select(ProductVariant).where(ProductVariant.product_id == product_id)
    )
    return result.scalars().all()


@router.post("/products/{product_id}/variants", response_model=ProductVariantResponse)
async def admin_create_product_variant(
    product_id: int,
    data: ProductVariantCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Add a variant to a product."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    result = await db.execute(
        select(ProductVariant).where(
            ProductVariant.product_id == product_id,
            ProductVariant.modification_type_id == data.modification_type_id,
            ProductVariant.value == data.value,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Такой вариант уже есть у товара")
    variant = ProductVariant(
        product_id=product_id,
        modification_type_id=data.modification_type_id,
        value=data.value,
        quantity=data.quantity,
    )
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return ProductVariantResponse.model_validate(variant)


@router.patch("/products/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
async def admin_update_product_variant(
    product_id: int,
    variant_id: int,
    data: ProductVariantUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update a product variant."""
    result = await db.execute(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(variant, key, value)
    await db.commit()
    await db.refresh(variant)
    return ProductVariantResponse.model_validate(variant)


@router.delete("/products/{product_id}/variants/{variant_id}")
async def admin_delete_product_variant(
    product_id: int,
    variant_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Delete a product variant."""
    result = await db.execute(
        select(ProductVariant).where(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product_id,
        )
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    await db.delete(variant)
    await db.commit()
    return {"ok": True}


@router.put("/products/{product_id}/variants", response_model=list[ProductVariantResponse])
async def admin_set_product_variants(
    product_id: int,
    items: list[ProductVariantCreate],
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Replace all variants for a product with the given list (by modification_type_id + value)."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.execute(delete(ProductVariant).where(ProductVariant.product_id == product_id))
    seen: set[tuple[int, str]] = set()
    for it in items:
        key = (it.modification_type_id, it.value)
        if key in seen:
            raise HTTPException(status_code=400, detail=f"Дубликат варианта: {it.value}")
        seen.add(key)
        v = ProductVariant(
            product_id=product_id,
            modification_type_id=it.modification_type_id,
            value=it.value,
            quantity=it.quantity,
        )
        db.add(v)
    # Синхронизация остатка товара с суммой остатков по модификациям
    product.stock_quantity = sum(it.quantity for it in items)
    await db.commit()
    result = await db.execute(
        select(ProductVariant).where(ProductVariant.product_id == product_id)
    )
    return [ProductVariantResponse.model_validate(r) for r in result.scalars().all()]


# ---- Promo codes ----

@router.get("/promos", response_model=list[PromoCodeResponse])
async def admin_get_promos(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Get all promo codes."""
    result = await db.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))
    return result.scalars().all()


@router.post("/promos", response_model=PromoCodeResponse)
async def admin_create_promo(
    data: PromoCodeCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Create a promo code."""
    promo = PromoCode(**data.model_dump())
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return PromoCodeResponse.model_validate(promo)


@router.delete("/promos/{promo_id}")
async def admin_delete_promo(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Delete a promo code."""
    promo = await db.get(PromoCode, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo not found")
    await db.delete(promo)
    await db.commit()
    return {"ok": True}


# ---- Banners ----

@router.get("/banners", response_model=list[BannerResponse])
async def admin_get_banners(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List all banners (including inactive), ordered by sort_order."""
    result = await db.execute(
        select(Banner).order_by(Banner.sort_order, Banner.id)
    )
    return [BannerResponse.model_validate(b) for b in result.scalars().all()]


@router.post("/banners/upload")
async def admin_upload_banner_image(
    file: UploadFile = File(...),
    admin: User = Depends(get_admin_user),
):
    """Upload an image for a banner. Returns { url: "/uploads/banners/..." }."""
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: jpg, png, webp, gif.",
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 50 MB.")
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    banner_dir = UPLOADS_DIR / "banners"
    banner_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = banner_dir / filename
    with open(file_path, "wb") as f:
        f.write(content)
    url = f"/uploads/banners/{filename}"
    return {"url": url}


@router.post("/banners", response_model=BannerResponse)
async def admin_create_banner(
    data: BannerCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Create a banner."""
    banner = Banner(**data.model_dump())
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    return BannerResponse.model_validate(banner)


@router.patch("/banners/{banner_id}", response_model=BannerResponse)
async def admin_update_banner(
    banner_id: int,
    data: BannerUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update a banner."""
    banner = await db.get(Banner, banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(banner, key, value)
    await db.commit()
    await db.refresh(banner)
    return BannerResponse.model_validate(banner)


@router.delete("/banners/{banner_id}")
async def admin_delete_banner(
    banner_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Delete a banner."""
    banner = await db.get(Banner, banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    await db.delete(banner)
    await db.commit()
    return {"ok": True}


# ---- Mailing ----

@router.post("/mailing")
async def admin_send_mailing(
    text: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Send a broadcast message to all users."""
    if not is_bot_configured():
        raise HTTPException(status_code=400, detail="Bot not configured — mailing unavailable")

    bot = get_bot()
    if not bot:
        raise HTTPException(status_code=400, detail="Bot not initialized")

    result = await db.execute(select(User.telegram_id))
    user_ids = result.scalars().all()

    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=text)
            sent += 1
        except Exception:
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(user_ids)}


# ---- Product Sync (MoySklad / 1C) ----

@router.post("/sync")
async def admin_sync_products(
    admin: User = Depends(get_admin_user),
):
    """Sync products from external source (MoySklad / 1C)."""
    if settings.product_source == ProductSource.DATABASE:
        raise HTTPException(
            status_code=400,
            detail="Product source is 'database' — nothing to sync. "
                   "Set PRODUCT_SOURCE=moysklad or PRODUCT_SOURCE=one_c in .env",
        )

    loader = get_product_loader()
    try:
        synced = await loader.sync_products()
        return {
            "ok": True,
            "source": settings.product_source.value,
            "synced": synced,
        }
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ---- Settings ----

@router.get("/settings")
async def admin_get_settings(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Get app settings."""
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        return {
            "shop_name": "My Shop",
            "pickup_enabled": True,
            "delivery_enabled": False,
            "currency": "RUB",
            "store_address": None,
            "delivery_city": None,
            "banner_aspect_shape": "rectangle",
            "banner_size": "medium",
            "category_image_size": "medium",
            "bonus_enabled": False,
            "bonus_welcome_enabled": False,
            "bonus_welcome_amount": 0,
            "bonus_purchase_enabled": False,
            "bonus_purchase_percent": 0,
            "bonus_spend_enabled": False,
            "bonus_spend_limit_type": "percent",
            "bonus_spend_limit_value": 0,
            "delivery_cost": 0,
            "free_delivery_min_amount": 0,
        }
    return {
        "shop_name": config.shop_name,
        "pickup_enabled": config.pickup_enabled,
        "delivery_enabled": config.delivery_enabled,
        "currency": config.currency,
        "store_address": config.store_address,
        "delivery_city": config.delivery_city,
        "delivery_cost": float(getattr(config, "delivery_cost", 0)),
        "free_delivery_min_amount": float(getattr(config, "free_delivery_min_amount", 0)),
        "banner_aspect_shape": getattr(config, "banner_aspect_shape", "rectangle"),
        "banner_size": getattr(config, "banner_size", "medium"),
        "category_image_size": getattr(config, "category_image_size", "medium"),
        "bonus_enabled": getattr(config, "bonus_enabled", False),
        "bonus_welcome_enabled": getattr(config, "bonus_welcome_enabled", False),
        "bonus_welcome_amount": float(getattr(config, "bonus_welcome_amount", 0)),
        "bonus_purchase_enabled": getattr(config, "bonus_purchase_enabled", False),
        "bonus_purchase_percent": float(getattr(config, "bonus_purchase_percent", 0)),
        "bonus_spend_enabled": getattr(config, "bonus_spend_enabled", False),
        "bonus_spend_limit_type": getattr(config, "bonus_spend_limit_type", "percent"),
        "bonus_spend_limit_value": float(getattr(config, "bonus_spend_limit_value", 0)),
    }


@router.patch("/settings")
async def admin_update_settings(
    data: dict,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Update app settings (JSON body)."""
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config:
        config = AppConfig()
        db.add(config)

    allowed = {
        "shop_name", "pickup_enabled", "delivery_enabled",
        "currency", "store_address", "delivery_city",
        "banner_aspect_shape", "banner_size", "category_image_size",
        "bonus_enabled", "bonus_welcome_enabled", "bonus_welcome_amount",
        "bonus_purchase_enabled", "bonus_purchase_percent",
        "bonus_spend_enabled",         "bonus_spend_limit_type", "bonus_spend_limit_value",
        "delivery_cost", "free_delivery_min_amount",
    }
    for key, value in data.items():
        if key not in allowed:
            continue
        if key in ("store_address", "delivery_city"):
            value = value.strip() if isinstance(value, str) and value.strip() else None
        if key in ("bonus_welcome_amount", "bonus_purchase_percent", "bonus_spend_limit_value", "delivery_cost", "free_delivery_min_amount"):
            value = float(value) if value is not None else 0
        setattr(config, key, value)

    await db.commit()
    return {"ok": True}

