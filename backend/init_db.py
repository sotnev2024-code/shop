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
    from app.db.models.product import Product
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

        # Products
        products = [
            # Electronics
            Product(name="Беспроводные наушники", description="Bluetooth наушники с шумоподавлением. Время работы до 30 часов.", price=4990, old_price=6990, category_id=categories[0].id, stock_quantity=50, image_url="https://picsum.photos/seed/headphones/400/400"),
            Product(name="Портативная колонка", description="Водонепроницаемая колонка с мощным басом. IPX7.", price=3490, category_id=categories[0].id, stock_quantity=30, image_url="https://picsum.photos/seed/speaker/400/400"),
            Product(name="Умные часы", description="Фитнес-трекер с GPS, пульсометром и SpO2.", price=8990, old_price=11990, category_id=categories[0].id, stock_quantity=20, image_url="https://picsum.photos/seed/smartwatch/400/400"),
            Product(name="Powerbank 20000 mAh", description="Быстрая зарядка USB-C PD 65W. Зарядит ноутбук.", price=2990, category_id=categories[0].id, stock_quantity=100, image_url="https://picsum.photos/seed/powerbank/400/400"),
            Product(name="Веб-камера 4K", description="Автофокус, микрофон, HDR. Идеальна для звонков.", price=5490, category_id=categories[0].id, stock_quantity=15, image_url="https://picsum.photos/seed/webcam/400/400"),

            # Clothing
            Product(name="Худи Oversize", description="Мягкое худи из плотного хлопка. Унисекс.", price=3990, category_id=categories[1].id, stock_quantity=40, image_url="https://picsum.photos/seed/hoodie/400/400"),
            Product(name="Кроссовки спортивные", description="Лёгкие беговые кроссовки с амортизацией.", price=6990, old_price=8990, category_id=categories[1].id, stock_quantity=25, image_url="https://picsum.photos/seed/sneakers/400/400"),
            Product(name="Футболка базовая", description="100% хлопок, плотность 180 г/м2.", price=1490, category_id=categories[1].id, stock_quantity=200, image_url="https://picsum.photos/seed/tshirt/400/400"),
            Product(name="Джинсы Slim Fit", description="Классические джинсы из эластичного денима.", price=4490, category_id=categories[1].id, stock_quantity=35, image_url="https://picsum.photos/seed/jeans/400/400"),

            # Home & Garden
            Product(name="Настольная лампа LED", description="Регулируемая яркость, 3 режима света. USB зарядка.", price=2490, category_id=categories[2].id, stock_quantity=60, image_url="https://picsum.photos/seed/lamp/400/400"),
            Product(name="Набор кухонных ножей", description="6 ножей из нержавеющей стали + подставка.", price=3990, old_price=5490, category_id=categories[2].id, stock_quantity=20, image_url="https://picsum.photos/seed/knives/400/400"),
            Product(name="Кофемашина капсульная", description="Давление 19 бар. Совместимость с Nespresso.", price=7990, category_id=categories[2].id, stock_quantity=10, image_url="https://picsum.photos/seed/coffee/400/400"),

            # Sports
            Product(name="Коврик для йоги", description="NBR 10мм, нескользящая поверхность. Чехол в комплекте.", price=1990, category_id=categories[3].id, stock_quantity=80, image_url="https://picsum.photos/seed/yogamat/400/400"),
            Product(name="Гантели разборные 20кг", description="Набор из 2 гантелей с регулируемым весом.", price=5990, category_id=categories[3].id, stock_quantity=15, image_url="https://picsum.photos/seed/dumbbells/400/400"),
            Product(name="Фитнес-браслет", description="Шагомер, пульс, калории, сон. До 14 дней без зарядки.", price=1990, old_price=2990, category_id=categories[3].id, stock_quantity=50, image_url="https://picsum.photos/seed/fitband/400/400"),

            # Books
            Product(name="Чистый код (Р. Мартин)", description="Классика программирования. Как писать хороший код.", price=890, category_id=categories[4].id, stock_quantity=100, image_url="https://picsum.photos/seed/cleancode/400/400"),
            Product(name="Думай медленно... решай быстро", description="Д. Канеман. О двух системах мышления.", price=690, category_id=categories[4].id, stock_quantity=70, image_url="https://picsum.photos/seed/thinking/400/400"),
        ]

        for product in products:
            db.add(product)

        # Promo codes
        from app.db.models.promo import PromoCode
        promos = [
            PromoCode(code="WELCOME10", discount_type="percent", discount_value=10, max_uses=100, is_active=True),
            PromoCode(code="SALE500", discount_type="fixed", discount_value=500, min_order_amount=3000, is_active=True),
        ]
        for promo in promos:
            db.add(promo)

        await db.commit()
        print(f"Seeded {len(products)} products, {len(categories)} categories, {len(promos)} promo codes!")


async def main():
    await create_tables()
    await seed_data()
    await engine.dispose()
    print("\nDatabase initialized! Ready to go.")


if __name__ == "__main__":
    asyncio.run(main())





