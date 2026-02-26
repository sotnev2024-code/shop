from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, or_, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.product import Product, product_category
from app.db.models.product_media import ProductMedia
from app.db.models.product_variant import ProductVariant
from app.db.models.category import Category
from app.db.models.favorite import Favorite
from app.db.models.user import User
from app.api.deps import get_current_user
from app.schemas.product import (
    ProductResponse, ProductListResponse, ProductMediaResponse,
    ModificationTypeShort, ProductVariantShort,
)

router = APIRouter()


def _build_media_list(product: Product) -> list[ProductMediaResponse]:
    """Build sorted media list: videos first, then images. Falls back to image_url."""
    media_items: list[ProductMediaResponse] = []

    if product.media:
        # Sort: videos first (lower sort_order), then images
        sorted_media = sorted(product.media, key=lambda m: m.sort_order)
        for m in sorted_media:
            media_items.append(ProductMediaResponse(
                id=m.id,
                media_type=m.media_type,
                url=m.file_path,
                sort_order=m.sort_order,
            ))

    # Fallback: if no ProductMedia records exist but image_url is set
    if not media_items and product.image_url:
        media_items.append(ProductMediaResponse(
            id=0,
            media_type="image",
            url=product.image_url,
            sort_order=0,
        ))

    return media_items


def _category_to_response_dict(category) -> dict | None:
    """Build category dict for ProductResponse without touching category.children (avoids lazy load)."""
    if not category:
        return None
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "sort_order": category.sort_order,
        "is_active": category.is_active,
        "parent_id": getattr(category, "parent_id", None),
        "children": [],
    }


def _build_variant_data(product: Product) -> tuple[ModificationTypeShort | None, list[ProductVariantShort]]:
    """Build modification_type and variants list for product response."""
    if not product.variants:
        return None, []
    mod_type = None
    short_variants: list[ProductVariantShort] = []
    for v in product.variants:
        if mod_type is None and v.modification_type:
            mod_type = ModificationTypeShort(id=v.modification_type.id, name=v.modification_type.name)
        short_variants.append(ProductVariantShort(value=v.value, quantity=v.quantity))
    return mod_type, short_variants


def _normalize_search(text: str) -> str:
    """Normalize search text: lowercase, ё→е, strip extra spaces."""
    text = text.lower().strip()
    text = text.replace("ё", "е")
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text


def _escape_like(value: str) -> str:
    """Escape % and _ for use in LIKE patterns."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _build_search_filters(search: str):
    """Build SQLAlchemy filters for smart search.
    Splits query into words and requires each word to match
    either name or description (case-insensitive).
    Uses COALESCE(description, '') so NULL description does not break the OR.
    """
    normalized = _normalize_search(search)
    if not normalized:
        return True  # no filter
    # Allow words of length 1+ so single letter/number search works
    words = [w for w in normalized.split() if w]

    if not words:
        pattern = f"%{normalized}%"
        escaped = _escape_like(search.strip())
        exact_pattern = f"%{escaped}%"
        # Match by normalized (lower) or by exact substring (helps when DB lower() doesn't handle Cyrillic)
        return or_(
            func.lower(Product.name).like(pattern),
            func.lower(func.coalesce(Product.description, "")).like(pattern),
            Product.name.like(exact_pattern, escape="\\"),
            func.coalesce(Product.description, "").like(exact_pattern, escape="\\"),
        )

    # Each word must appear in name or description
    word_filters = []
    for word in words:
        pattern = f"%{word}%"
        word_filters.append(
            or_(
                func.lower(Product.name).like(pattern),
                func.lower(func.coalesce(Product.description, "")).like(pattern),
            )
        )
    return and_(*word_filters)


@router.get("/products", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    sort_by: str = Query("created_at", pattern="^(price|name|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get paginated products with filters."""
    # In-stock: either product.stock_quantity > 0 or has at least one variant with quantity > 0
    has_variant_stock = (
        select(ProductVariant.id)
        .where(
            ProductVariant.product_id == Product.id,
            ProductVariant.quantity > 0,
        )
        .correlate(Product)
        .exists()
    )
    query = select(Product).where(
        Product.is_available == True,
        or_(Product.stock_quantity > 0, has_variant_stock),
    )

    # Filters: category_id and all its descendants (subcategories); product can be in any of these
    if category_id is not None:
        category_ids_cte = (
            select(Category.id).where(Category.id == category_id).cte(recursive=True)
        )
        category_ids_cte = category_ids_cte.union_all(
            select(Category.id).where(Category.parent_id == category_ids_cte.c.id)
        )
        product_ids_in_cat = select(product_category.c.product_id).where(
            product_category.c.category_id.in_(select(category_ids_cte.c.id))
        )
        query = query.where(Product.id.in_(product_ids_in_cat))
    if search:
        query = query.where(_build_search_filters(search))
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sorting
    sort_column = getattr(Product, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    query = query.options(
        selectinload(Product.categories),
        selectinload(Product.media),
        selectinload(Product.variants).selectinload(ProductVariant.modification_type),
    )

    result = await db.execute(query)
    products = result.scalars().all()

    # Check favorites
    if products:
        product_ids = [p.id for p in products]
        fav_result = await db.execute(
            select(Favorite.product_id).where(
                Favorite.user_id == user.id,
                Favorite.product_id.in_(product_ids),
            )
        )
        fav_ids = set(fav_result.scalars().all())
    else:
        fav_ids = set()

    items = []
    for p in products:
        mod_type, variants_short = _build_variant_data(p)
        cats = getattr(p, "categories", None) or []
        first_cat = cats[0] if cats else None
        resp = ProductResponse.model_validate({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": round(float(p.price), 2),
            "old_price": round(float(getattr(p, "old_price", None)), 2) if getattr(p, "old_price", None) is not None else None,
            "image_url": p.image_url,
            "is_available": p.is_available,
            "stock_quantity": p.stock_quantity,
            "category_ids": [c.id for c in cats],
            "external_id": getattr(p, "external_id", None),
            "created_at": p.created_at,
            "category_id": first_cat.id if first_cat else None,
            "category": _category_to_response_dict(first_cat),
            "categories": [_category_to_response_dict(c) for c in cats],
            "is_favorite": p.id in fav_ids,
            "media": _build_media_list(p),
            "modification_type": mod_type,
            "variants": variants_short,
        })
        items.append(resp)

    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single product by id."""
    result = await db.execute(
        select(Product)
        .where(Product.id == product_id)
        .options(
            selectinload(Product.categories),
            selectinload(Product.media),
            selectinload(Product.variants).selectinload(ProductVariant.modification_type),
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check favorite
    fav_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.product_id == product_id,
        )
    )
    is_fav = fav_result.scalar_one_or_none() is not None

    mod_type, variants_short = _build_variant_data(product)
    cats = getattr(product, "categories", None) or []
    first_cat = cats[0] if cats else None
    return ProductResponse.model_validate({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": round(float(product.price), 2),
        "old_price": round(float(getattr(product, "old_price", None)), 2) if getattr(product, "old_price", None) is not None else None,
        "image_url": product.image_url,
        "is_available": product.is_available,
        "stock_quantity": product.stock_quantity,
        "category_ids": [c.id for c in cats],
        "external_id": getattr(product, "external_id", None),
        "created_at": product.created_at,
        "category_id": first_cat.id if first_cat else None,
        "category": _category_to_response_dict(first_cat),
        "categories": [_category_to_response_dict(c) for c in cats],
        "is_favorite": is_fav,
        "media": _build_media_list(product),
        "modification_type": mod_type,
        "variants": variants_short,
    })
