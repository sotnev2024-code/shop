from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.category import Category
from app.db.models.product import Product
from app.db.models.product_variant import ProductVariant
from app.schemas.product import CategoryResponse

router = APIRouter()


def _category_has_stock():
    """Category has at least one product that is in stock (by product.stock or by variant)."""
    has_variant_stock = (
        select(ProductVariant.id)
        .where(
            ProductVariant.product_id == Product.id,
            ProductVariant.quantity > 0,
        )
        .correlate(Product)
        .exists()
    )
    return (
        select(Product.id)
        .where(
            Product.category_id == Category.id,
            Product.is_available == True,
            or_(Product.stock_quantity > 0, has_variant_stock),
        )
        .correlate(Category)
        .exists()
    )


def _build_category_tree(
    categories: list[Category],
    has_stock_ids: set[int],
    visible_ids: set[int],
    parent_id: int | None = None,
    seen_all_ids: set[int] | None = None,
) -> list[CategoryResponse]:
    """Build tree of CategoryResponse for categories under parent_id. seen_all_ids — чтобы категория «Все» (slug all) не дублировалась."""
    if seen_all_ids is None:
        seen_all_ids = set()
    out = []
    for c in categories:
        if c.parent_id != parent_id:
            continue
        if c.id not in visible_ids:
            continue
        if c.slug == "all" and c.id in seen_all_ids:
            continue
        if c.slug == "all":
            seen_all_ids.add(c.id)
        children = _build_category_tree(categories, has_stock_ids, visible_ids, c.id, seen_all_ids)
        out.append(
            CategoryResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                sort_order=c.sort_order,
                is_active=c.is_active,
                parent_id=c.parent_id,
                image_url=getattr(c, "image_url", None),
                children=children,
            )
        )
    return sorted(out, key=lambda x: (x.sort_order, x.name))


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get active categories as tree (roots with children). Only categories with in-stock products or with such descendants."""
    # Категория «Все» (slug all) создаётся при первом запросе, если её нет
    result = await db.execute(select(Category).where(Category.slug == "all"))
    if result.scalar_one_or_none() is None:
        db.add(Category(name="Все", slug="all", sort_order=0, is_active=True, parent_id=None))
        await db.commit()
    has_in_stock = _category_has_stock()
    # Categories that have at least one in-stock product
    result = await db.execute(
        select(Category.id).where(Category.is_active == True, has_in_stock)
    )
    ids_with_stock = {r for r, in result.all()}
    # Load all active categories
    result = await db.execute(
        select(Category)
        .where(Category.is_active == True)
        .order_by(Category.sort_order, Category.name)
    )
    all_categories = result.scalars().all()
    # Visible = has stock or any descendant has stock (add all ancestors of ids_with_stock)
    visible_ids = set(ids_with_stock)
    for c in all_categories:
        if c.parent_id and c.parent_id in visible_ids:
            visible_ids.add(c.id)
    # Add ancestors until no change
    changed = True
    while changed:
        changed = False
        for c in all_categories:
            if c.id in visible_ids and c.parent_id and c.parent_id not in visible_ids:
                visible_ids.add(c.parent_id)
                changed = True
    # Всегда показывать категорию «Все» (slug all) в каталоге, если она есть и активна
    for c in all_categories:
        if c.slug == "all" and c.is_active:
            visible_ids.add(c.id)
            break
    # Build tree (roots only)
    return _build_category_tree(all_categories, ids_with_stock, visible_ids, parent_id=None)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single category by id."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse(
        id=category.id,
        name=category.name,
        slug=category.slug,
        sort_order=category.sort_order,
        is_active=category.is_active,
        parent_id=category.parent_id,
        image_url=getattr(category, "image_url", None),
        children=[],
    )

