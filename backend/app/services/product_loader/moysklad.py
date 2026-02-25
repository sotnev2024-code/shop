from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings
from app.services.product_loader.base import BaseProductLoader

logger = logging.getLogger(__name__)


class MoySkladLoader(BaseProductLoader):
    """Load products from Мой Склад API.

    Images are NOT downloaded locally — we resolve the public CDN URLs
    from MoySklad and store them directly.  Only admin-uploaded media
    goes to the local ``uploads/`` directory.
    """

    BASE_URL = "https://api.moysklad.ru/api/remap/1.2"

    def __init__(self):
        self.token = settings.moysklad_token
        self.headers = {"Authorization": f"Bearer {self.token}"}

    # ------------------------------------------------------------------
    # Image helpers
    # ------------------------------------------------------------------

    async def _get_all_image_urls(
        self, client: httpx.AsyncClient, product_meta: dict
    ) -> list[str]:
        """Return public CDN URLs for ALL images of a product.

        MoySklad ``downloadHref`` redirects to a public URL on
        ``miniature-prod.moysklad.ru`` — we follow the redirect and
        store the final URL so the browser can load images directly.
        """
        images_meta = product_meta.get("images", {}).get("meta", {})
        if images_meta.get("size", 0) == 0:
            return []

        images_href = images_meta.get("href")
        if not images_href:
            return []

        urls: list[str] = []
        try:
            resp = await client.get(images_href, headers=self.headers)
            if resp.status_code != 200:
                return []

            rows = resp.json().get("rows", [])
            for row in rows:
                # Prefer miniature downloadHref → resolve to CDN URL
                download_href = (
                    row.get("miniature", {}).get("downloadHref")
                    or row.get("miniature", {}).get("href")
                )
                if not download_href:
                    download_href = row.get("tiny", {}).get("downloadHref")
                if not download_href:
                    continue

                cdn_url = await self._resolve_cdn_url(client, download_href)
                if cdn_url:
                    urls.append(cdn_url)
        except Exception as e:
            logger.warning(f"Failed to fetch images meta: {e}")
        return urls

    async def _resolve_cdn_url(
        self, client: httpx.AsyncClient, download_href: str
    ) -> str | None:
        """Follow MoySklad download redirect to get the public CDN URL.

        MoySklad ``downloadHref`` responds with a 302 redirect to a
        permanent, publicly-accessible URL on ``miniature-prod.moysklad.ru``.
        We do a streaming GET so we don't download the full image body.
        """
        try:
            async with client.stream(
                "GET",
                download_href,
                headers=self.headers,
                follow_redirects=True,
            ) as resp:
                if resp.status_code == 200:
                    final_url = str(resp.url)
                    return final_url
        except Exception as e:
            logger.debug(f"Failed to resolve CDN URL: {e}")
        return None

    # ------------------------------------------------------------------
    # Stock
    # ------------------------------------------------------------------

    async def _get_stock(self, client: httpx.AsyncClient) -> dict[str, float]:
        """Fetch current stock quantities (with pagination)."""
        stock_map: dict[str, float] = {}
        offset = 0
        page_size = 1000
        try:
            while True:
                resp = await client.get(
                    f"{self.BASE_URL}/report/stock/all",
                    headers=self.headers,
                    params={"limit": page_size, "offset": offset},
                )
                if resp.status_code != 200:
                    logger.warning(f"Stock API error {resp.status_code}")
                    break

                data = resp.json()
                rows = data.get("rows", [])
                for row in rows:
                    assortment_href = row.get("meta", {}).get("href", "")
                    if "/entity/product/" in assortment_href:
                        pid = assortment_href.split("/entity/product/")[-1]
                        # Strip query parameters (e.g. ?expand=supplier)
                        if "?" in pid:
                            pid = pid.split("?")[0]
                        stock_map[pid] = row.get("quantity", 0)

                total = data.get("meta", {}).get("size", 0)
                offset += page_size
                if offset >= total or len(rows) == 0:
                    break

            logger.info(f"MoySklad: fetched stock for {len(stock_map)} products")
        except Exception as e:
            logger.warning(f"Failed to fetch stock: {e}")
        return stock_map

    # ------------------------------------------------------------------
    # Load & Sync
    # ------------------------------------------------------------------

    async def load_products(self) -> list[dict[str, Any]]:
        """Fetch product data + stock from MoySklad.

        Image URLs are resolved to public CDN links stored in
        ``_image_urls`` (no local download needed).
        """
        if not self.token:
            logger.warning("MoySklad token not configured")
            return []

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Fetch ALL products with pagination
            all_rows: list[dict] = []
            offset = 0
            page_size = 1000

            while True:
                response = await client.get(
                    f"{self.BASE_URL}/entity/product",
                    headers=self.headers,
                    params={"limit": page_size, "offset": offset},
                )
                if response.status_code != 200:
                    logger.error(
                        f"MoySklad API error {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    break

                data = response.json()
                rows = data.get("rows", [])
                all_rows.extend(rows)
                logger.info(
                    f"MoySklad: fetched {len(all_rows)}/"
                    f"{data.get('meta', {}).get('size', '?')} products"
                )

                total = data.get("meta", {}).get("size", 0)
                if len(all_rows) >= total or len(rows) == 0:
                    break
                offset += page_size

            if not all_rows:
                return []

            # Fetch stock
            stock_map = await self._get_stock(client)

            products = []
            for row in all_rows:
                price = 0.0
                sale_prices = row.get("salePrices", [])
                if sale_prices:
                    price = sale_prices[0].get("value", 0) / 100

                product_id = row.get("id", "")

                # Resolve image CDN URLs (no download — just URL resolution)
                image_urls = await self._get_all_image_urls(client, row)

                path_name = row.get("pathName", "").strip()
                category_name = (
                    path_name.split("/")[-1].strip() if path_name else None
                )

                products.append(
                    {
                        "external_id": product_id,
                        "name": row.get("name", ""),
                        "description": row.get("description", ""),
                        "price": price,
                        "image_urls": image_urls,
                        "stock_quantity": int(stock_map.get(product_id, 0)),
                        "category_name": category_name,
                    }
                )
            return products

    async def sync_products(self) -> int:
        from sqlalchemy import select, delete as sql_delete
        from app.db.session import async_session
        from app.db.models.product import Product, product_category
        from app.db.models.product_media import ProductMedia
        from app.db.models.category import Category

        products_data = await self.load_products()
        if not products_data:
            logger.warning("MoySklad sync: no products loaded")
            return 0

        async with async_session() as db:
            # Build category cache
            category_cache: dict[str, int] = {}
            result = await db.execute(select(Category))
            for cat in result.scalars().all():
                category_cache[cat.name] = cat.id

            synced = 0

            for item in products_data:
                # Ensure category exists
                cat_name = item.get("category_name")
                cat_id = None
                if cat_name:
                    if cat_name not in category_cache:
                        new_cat = Category(
                            name=cat_name,
                            slug=cat_name.lower().replace(" ", "-"),
                        )
                        db.add(new_cat)
                        await db.flush()
                        category_cache[cat_name] = new_cat.id
                    cat_id = category_cache[cat_name]

                # Upsert product
                result = await db.execute(
                    select(Product).where(
                        Product.external_id == item["external_id"]
                    )
                )
                existing = result.scalar_one_or_none()

                is_available = item["stock_quantity"] > 0
                image_urls = item.get("image_urls", [])

                if existing:
                    existing.name = item["name"]
                    existing.description = item["description"]
                    existing.price = item["price"]
                    existing.stock_quantity = item["stock_quantity"]
                    existing.is_available = is_available
                    await db.execute(
                        product_category.delete().where(
                            product_category.c.product_id == existing.id
                        )
                    )
                    if cat_id:
                        await db.execute(
                            product_category.insert().values(
                                product_id=existing.id, category_id=cat_id
                            )
                        )

                    # Check if admin uploaded local media for this product
                    local_media_q = await db.execute(
                        select(ProductMedia).where(
                            ProductMedia.product_id == existing.id,
                            ~ProductMedia.file_path.like("http%"),
                        )
                    )
                    has_local_media = local_media_q.scalars().first() is not None

                    # Only update remote URLs if admin hasn't added local media
                    if not has_local_media:
                        # Remove old remote-URL media
                        await db.execute(
                            sql_delete(ProductMedia).where(
                                ProductMedia.product_id == existing.id,
                                ProductMedia.file_path.like("http%"),
                            )
                        )
                        # Store resolved CDN URLs directly
                        for idx, url in enumerate(image_urls):
                            db.add(
                                ProductMedia(
                                    product_id=existing.id,
                                    media_type="image",
                                    file_path=url,
                                    sort_order=idx,
                                )
                            )
                        if image_urls:
                            existing.image_url = image_urls[0]
                else:
                    product = Product(
                        name=item["name"],
                        description=item["description"],
                        price=item["price"],
                        external_id=item["external_id"],
                        stock_quantity=item["stock_quantity"],
                        is_available=is_available,
                        image_url=image_urls[0] if image_urls else None,
                    )
                    db.add(product)
                    await db.flush()
                    if cat_id:
                        await db.execute(
                            product_category.insert().values(
                                product_id=product.id, category_id=cat_id
                            )
                        )

                    # Store resolved CDN URLs directly
                    for idx, url in enumerate(image_urls):
                        db.add(
                            ProductMedia(
                                product_id=product.id,
                                media_type="image",
                                file_path=url,
                                sort_order=idx,
                            )
                        )

                synced += 1

            await db.commit()
            logger.info(f"MoySklad sync complete: {synced} products synced")
        return synced
