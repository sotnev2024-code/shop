from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.favorite import Favorite
from app.db.models.product import Product
from app.db.models.product_variant import ProductVariant
from app.db.models.user import User
from app.api.deps import get_current_user
from app.schemas.product import ProductResponse
from app.api.v1.products import _build_media_list, _build_variant_data, _category_to_response_dict

router = APIRouter()


@router.get("/favorites", response_model=list[ProductResponse])
async def get_favorites(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get user's favorites."""
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_id == user.id)
        .options(
            selectinload(Favorite.product).selectinload(Product.category),
            selectinload(Favorite.product).selectinload(Product.media),
            selectinload(Favorite.product).selectinload(Product.variants).selectinload(ProductVariant.modification_type),
        )
    )
    favorites = result.scalars().all()

    items = []
    for fav in favorites:
        p = fav.product
        mod_type, variants_short = _build_variant_data(p)
        items.append(ProductResponse.model_validate({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price,
            "old_price": getattr(p, "old_price", None),
            "image_url": p.image_url,
            "is_available": p.is_available,
            "stock_quantity": p.stock_quantity,
            "category_id": p.category_id,
            "external_id": getattr(p, "external_id", None),
            "created_at": p.created_at,
            "category": _category_to_response_dict(p.category) if p.category else None,
            "is_favorite": True,
            "media": _build_media_list(p),
            "modification_type": mod_type,
            "variants": variants_short,
        }))
    return items


@router.post("/favorites/validate")
async def validate_favorites(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove from favorites products that are no longer in stock (is_available=False or stock_quantity=0)."""
    result = await db.execute(
        select(Favorite)
        .where(Favorite.user_id == user.id)
        .options(selectinload(Favorite.product)),
    )
    favorites = result.scalars().all()

    removed: list[dict] = []
    for fav in favorites:
        p = fav.product
        if not p or not p.is_available or (getattr(p, "stock_quantity", 0) or 0) <= 0:
            removed.append({
                "product_id": fav.product_id,
                "product_name": p.name if p else "Удалённый товар",
            })
            await db.delete(fav)

    await db.commit()
    return {"removed": removed}


@router.post("/favorites/{product_id}")
async def add_to_favorites(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Add product to favorites."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if already in favorites
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.product_id == product_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {"ok": True, "message": "Already in favorites"}

    fav = Favorite(user_id=user.id, product_id=product_id)
    db.add(fav)
    await db.commit()
    return {"ok": True}


@router.delete("/favorites/{product_id}")
async def remove_from_favorites(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Remove product from favorites."""
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.product_id == product_id,
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=404, detail="Not in favorites")

    await db.delete(fav)
    await db.commit()
    return {"ok": True}

