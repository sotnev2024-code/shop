from typing import Any

import httpx

from app.config import settings
from app.services.product_loader.base import BaseProductLoader


class OneCLoader(BaseProductLoader):
    """Load products from 1C API."""

    def __init__(self):
        self.endpoint = settings.one_c_endpoint
        self.login = settings.one_c_login
        self.password = settings.one_c_password

    async def load_products(self) -> list[dict[str, Any]]:
        if not self.endpoint:
            return []

        auth = None
        if self.login and self.password:
            auth = (self.login, self.password)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.endpoint}/products",
                    auth=auth,
                    timeout=30,
                )
                if response.status_code != 200:
                    return []

                data = response.json()
                products = []
                for item in data if isinstance(data, list) else data.get("value", []):
                    products.append({
                        "external_id": str(item.get("Ref_Key", item.get("id", ""))),
                        "name": item.get("Description", item.get("name", "")),
                        "description": item.get("Описание", item.get("description", "")),
                        "price": float(item.get("Цена", item.get("price", 0))),
                        "image_url": None,
                        "stock_quantity": int(item.get("Остаток", item.get("stock", 0))),
                    })
                return products
            except Exception:
                return []

    async def sync_products(self) -> int:
        from sqlalchemy import select
        from app.db.session import async_session
        from app.db.models.product import Product

        products_data = await self.load_products()
        if not products_data:
            return 0

        async with async_session() as db:
            synced = 0
            for item in products_data:
                result = await db.execute(
                    select(Product).where(Product.external_id == item["external_id"])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    existing.name = item["name"]
                    existing.description = item["description"]
                    existing.price = item["price"]
                    existing.stock_quantity = item["stock_quantity"]
                else:
                    product = Product(
                        name=item["name"],
                        description=item["description"],
                        price=item["price"],
                        external_id=item["external_id"],
                        stock_quantity=item["stock_quantity"],
                        is_available=True,
                    )
                    db.add(product)
                synced += 1

            await db.commit()
        return synced





