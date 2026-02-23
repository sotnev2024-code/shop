import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings, ProductSource
from app.bot.bot import get_bot, dp, setup_bot, is_bot_configured

try:
    from aiogram.exceptions import TelegramNetworkError
except ImportError:
    TelegramNetworkError = Exception
try:
    from aiohttp.client_exceptions import ServerDisconnectedError, ClientError
except ImportError:
    ServerDisconnectedError = ConnectionError
    ClientError = ConnectionError
from app.api.v1 import products, categories, cart, favorites, orders, payments, promo, config, admin, owner, banners, user as user_router

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _periodic_sync():
    """Background job: sync products from external source."""
    try:
        from app.services.product_loader import get_product_loader
        loader = get_product_loader()
        synced = await loader.sync_products()
        logger.info(f"Periodic sync complete: {synced} products synced from {settings.product_source.value}")
    except Exception as e:
        logger.error(f"Periodic product sync failed: {e}", exc_info=True)


async def _ensure_tables():
    """Create missing tables on startup (idempotent)."""
    from app.db.base import Base
    from app.db.session import engine
    import app.db.models  # noqa — register all models

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured.")
    except Exception as e:
        logger.error(
            f"Failed to ensure database tables: {e}\n"
            f"Database URL: {settings.database_url}\n"
            "For local dev, use: DATABASE_URL=sqlite+aiosqlite:///./shop.db"
        )
        raise


def _asyncio_exception_handler(loop, context):
    """Log unhandled task exceptions (e.g. from bot polling) so they don't spam 'never retrieved'."""
    exc = context.get("exception")
    if exc is not None:
        logger.warning("Async task error (bot/background): %s", exc, exc_info=exc)
    else:
        logger.warning("Async context: %s", context)


@asynccontextmanager
async def lifespan(application: FastAPI):
    asyncio.get_running_loop().set_exception_handler(_asyncio_exception_handler)

    # Startup — ensure DB tables exist
    await _ensure_tables()

    polling_task = None
    if is_bot_configured():
        await setup_bot()
        bot = get_bot()

        async def _polling_with_recovery():
            """Run bot polling; on network errors log and retry so the API process stays up."""
            while True:
                try:
                    await dp.start_polling(bot)
                    break
                except asyncio.CancelledError:
                    raise
                except (
                    TelegramNetworkError,
                    ConnectionError,
                    OSError,
                    ServerDisconnectedError,
                    ClientError,
                ) as e:
                    logger.warning(
                        "Bot polling network error (API keeps running): %s. Retry in 30s.",
                        e,
                    )
                    await asyncio.sleep(30)
                except Exception as e:
                    logger.exception("Bot polling error. Retry in 30s: %s", e)
                    await asyncio.sleep(30)

        polling_task = asyncio.create_task(_polling_with_recovery())
        logger.info("Bot polling started!")
    else:
        logger.warning(
            "Bot token not configured — running API only (no Telegram bot). "
            "Set BOT_TOKEN in .env to enable the bot."
        )
    # Auto-sync products from external source on startup
    if settings.product_source != ProductSource.DATABASE:
        logger.info(f"Product source: {settings.product_source.value} — starting initial sync...")
        try:
            from app.services.product_loader import get_product_loader
            loader = get_product_loader()
            synced = await loader.sync_products()
            logger.info(f"Initial sync complete: {synced} products synced from {settings.product_source.value}")
        except Exception as e:
            logger.error(f"Initial product sync failed: {e}", exc_info=True)

        # Start periodic sync scheduler
        interval = settings.sync_interval_minutes
        if interval > 0:
            scheduler.add_job(_periodic_sync, "interval", minutes=interval, id="product_sync")
            scheduler.start()
            logger.info(f"Periodic sync scheduler started: every {interval} minutes")

    yield
    # Shutdown
    if scheduler.running:
        scheduler.shutdown(wait=False)
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except (asyncio.CancelledError, Exception) as e:
            logger.debug(f"Polling task stopped: {e}")
        try:
            bot = get_bot()
            if bot:
                await bot.session.close()
        except Exception as e:
            logger.debug(f"Bot session close: {e}")


app = FastAPI(
    title="Shop Mini App API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded media files
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# API routes
app.include_router(config.router, prefix="/api/v1", tags=["config"])
app.include_router(user_router.router, prefix="/api/v1/user", tags=["user"])
app.include_router(products.router, prefix="/api/v1", tags=["products"])
app.include_router(categories.router, prefix="/api/v1", tags=["categories"])
app.include_router(cart.router, prefix="/api/v1", tags=["cart"])
app.include_router(favorites.router, prefix="/api/v1", tags=["favorites"])
app.include_router(orders.router, prefix="/api/v1", tags=["orders"])
app.include_router(payments.router, prefix="/api/v1", tags=["payments"])
app.include_router(promo.router, prefix="/api/v1", tags=["promo"])
app.include_router(banners.router, prefix="/api/v1", tags=["banners"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(owner.router, prefix="/api/v1/owner", tags=["owner"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
