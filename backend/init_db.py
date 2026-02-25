"""
Initialize database with tables and sample data for testing.
Run: python init_db.py
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.db.base import Base
from app.db.session import engine, async_session
from app.db.models import *  # noqa


async def create_tables():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")


async def seed_data():
    """Insert sample data for testing."""
    from app.db.models.category import Category
    from app.db.models.product import Product, product_category
    from app.db.models.app_config import AppConfig

    async with async_session() as db:
        # Check if data already exists
        from sqlalchemy import select, func
        count = (await db.execute(select(func.count(Product.id)))).scalar()
        if count and count > 0:
            print(f"Database already has {count} products. Skipping seed.")
            return

        # App config
        config = AppConfig(
            shop_name="Demo Shop",
            checkout_type="basic",
            product_source="database",
            delivery_enabled=False,
            pickup_enabled=True,
            promo_enabled=True,
            mailing_enabled=True,
            currency="RUB",
        )
        db.add(config)

        # Categories
        categories = [
            Category(name="Электроника", slug="electronics", sort_order=1),
            Category(name="Одежда", slug="clothing", sort_order=2),
            Category(name="Дом и сад", slug="home-garden", sort_order=3),
            Category(name="Спорт", slug="sports", sort_order=4),
            Category(name="Книги", slug="books", sort_order=5),
        ]
        for cat in categories:
            db.add(cat)
        await db.flush()

        # Products: (name, description, price, old_price, stock, image_url, category_index)
        product_rows = [
            ("Беспроводные наушники", "Bluetooth наушники с шумоподавлением. Время работы до 30 часов.", 4990, 6990, 50, "https://picsum.photos/seed/headphones/400/400", 0),
            ("Портативная колонка", "Водонепроницаемая колонка с мощным басом. IPX7.", 3490, None, 30, "https://picsum.photos/seed/speaker/400/400", 0),
            ("Умные часы", "Фитнес-трекер с GPS, пульсометром и SpO2.", 8990, 11990, 20, "https://picsum.photos/seed/smartwatch/400/400", 0),
            ("Powerbank 20000 mAh", "Быстрая зарядка USB-C PD 65W. Зарядит ноутбук.", 2990, None, 100, "https://picsum.photos/seed/powerbank/400/400", 0),
            ("Веб-камера 4K", "Автофокус, микрофон, HDR. Идеальна для звонков.", 5490, None, 15, "https://picsum.photos/seed/webcam/400/400", 0),
            ("Худи Oversize", "Мягкое худи из плотного хлопка. Унисекс.", 3990, None, 40, "https://picsum.photos/seed/hoodie/400/400", 1),
            ("Кроссовки спортивные", "Лёгкие беговые кроссовки с амортизацией.", 6990, 8990, 25, "https://picsum.photos/seed/sneakers/400/400", 1),
            ("Футболка базовая", "100% хлопок, плотность 180 г/м2.", 1490, None, 200, "https://picsum.photos/seed/tshirt/400/400", 1),
            ("Джинсы Slim Fit", "Классические джинсы из эластичного денима.", 4490, None, 35, "https://picsum.photos/seed/jeans/400/400", 1),
            ("Настольная лампа LED", "Регулируемая яркость, 3 режима света. USB зарядка.", 2490, None, 60, "https://picsum.photos/seed/lamp/400/400", 2),
            ("Набор кухонных ножей", "6 ножей из нержавеющей стали + подставка.", 3990, 5490, 20, "https://picsum.photos/seed/knives/400/400", 2),
            ("Кофемашина капсульная", "Давление 19 бар. Совместимость с Nespresso.", 7990, None, 10, "https://picsum.photos/seed/coffee/400/400", 2),
            ("Коврик для йоги", "NBR 10мм, нескользящая поверхность. Чехол в комплекте.", 1990, None, 80, "https://picsum.photos/seed/yogamat/400/400", 3),
            ("Гантели разборные 20кг", "Набор из 2 гантелей с регулируемым весом.", 5990, None, 15, "https://picsum.photos/seed/dumbbells/400/400", 3),
            ("Фитнес-браслет", "Шагомер, пульс, калории, сон. До 14 дней без зарядки.", 1990, 2990, 50, "https://picsum.photos/seed/fitband/400/400", 3),
            ("Чистый код (Р. Мартин)", "Классика программирования. Как писать хороший код.", 890, None, 100, "https://picsum.photos/seed/cleancode/400/400", 4),
            ("Думай медленно... решай быстро", "Д. Канеман. О двух системах мышления.", 690, None, 70, "https://picsum.photos/seed/thinking/400/400", 4),
        ]
        for name, desc, price, old_price, stock, img, cat_idx in product_rows:
            product = Product(
                name=name,
                description=desc,
                price=price,
                old_price=old_price,
                stock_quantity=stock,
                image_url=img,
            )
            db.add(product)
            await db.flush()
            await db.execute(
                product_category.insert().values(
                    product_id=product.id, category_id=categories[cat_idx].id
                )
            )

        # Promo codes
        from app.db.models.promo import PromoCode
        promos = [
            PromoCode(code="WELCOME10", discount_type="percent", discount_value=10, max_uses=100, is_active=True),
            PromoCode(code="SALE500", discount_type="fixed", discount_value=500, min_order_amount=3000, is_active=True),
        ]
        for promo in promos:
            db.add(promo)

        await db.commit()
        print(f"Seeded {len(product_rows)} products, {len(categories)} categories, {len(promos)} promo codes!")


async def main():
    await create_tables()
    await seed_data()
    await engine.dispose()
    print("\nDatabase initialized! Ready to go.")


if __name__ == "__main__":
    asyncio.run(main())





