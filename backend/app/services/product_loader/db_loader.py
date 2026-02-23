from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.product import Product
from app.services.product_loader.base import BaseProductLoader


class DatabaseLoader(BaseProductLoader):
    """Load products directly from the database."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_products(self) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(Product).where(Product.is_available == True)
        )
        products = result.scalars().all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "description": p.description,
                "image_url": p.image_url,
                "stock_quantity": p.stock_quantity,
                "category_id": p.category_id,
            }
            for p in products
        ]

    async def sync_products(self) -> int:
        # No sync needed for database source
        return 0





