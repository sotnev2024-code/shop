import asyncio
import logging
import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings, ProductSource
from app.bot.bot import get_bot, dp, setup_bot, is_bot_configured
from app.db.session import get_db
from app.db.models.error_log import ErrorLog

try:
    from aiogram.exceptions import TelegramNetworkError
except ImportError:
    TelegramNetworkError = Exception
try:
    from aiohttp.client_exceptions import ServerDisconnectedError, ClientError
except ImportError:
    ServerDisconnectedError = ConnectionError
    ClientError = ConnectionError
from app.api.v1 import (
    products,
    categories,
    cart,
    favorites,
    orders,
    payments,
    promo,
    config,
    admin,
    owner,
    banners,
    user as user_router,
    football,
    errors as errors_router,
)

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
        try:
            from app.db.session import async_session
            from app.services.error_log_service import log_error, format_exception_traceback
            async with async_session() as db:
                await log_error(db, str(e), "ERROR", path="job:sync", source="job", traceback_str=format_exception_traceback(e))
        except Exception:
            pass


async def _daily_matches_job():
    """Background job: send daily matches to forum at 12:00."""
    try:
        from app.db.session import async_session
        from app.services.daily_matches_service import send_daily_matches
        async with async_session() as db:
            await send_daily_matches(db)
    except Exception as e:
        logger.error("Daily matches job failed: %s", e, exc_info=True)
        try:
            from app.db.session import async_session
            from app.services.error_log_service import log_error, format_exception_traceback
            async with async_session() as db:
                await log_error(db, str(e), "ERROR", path="job:daily_matches", source="job", traceback_str=format_exception_traceback(e))
        except Exception:
            pass


async def _autopost_job():
    """Background job: post product to channel at configured times."""
    try:
        import json
        from datetime import datetime
        from sqlalchemy import select
        from app.db.session import async_session
        from app.db.models.app_config import AppConfig
        from app.services.autopost_service import run_autopost

        async with async_session() as db:
            result = await db.execute(select(AppConfig).limit(1))
            config = result.scalar_one_or_none()
            if not config or not getattr(config, "autopost_enabled", False):
                return
            raw_times = getattr(config, "autopost_times", None) or "[]"
            try:
                times = json.loads(raw_times) if isinstance(raw_times, str) else raw_times
            except (json.JSONDecodeError, TypeError):
                times = ["13:00", "19:00"]
            posts_per_day = max(1, min(10, getattr(config, "autopost_posts_per_day", 2) or 2))
            times = times[:posts_per_day] if isinstance(times, list) else []

            now = datetime.now()
            current = now.strftime("%H:%M")
            if current in times:
                await run_autopost(db)
    except Exception as e:
        logger.error("Autopost job failed: %s", e, exc_info=True)
        try:
            from app.db.session import async_session
            from app.services.error_log_service import log_error, format_exception_traceback
            async with async_session() as db:
                await log_error(db, str(e), "ERROR", path="job:autopost", source="job", traceback_str=format_exception_traceback(e))
        except Exception:
            pass


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


async def _log_async_error(message: str, source: str, tb_parts: list):
    """Log error to DB from async context."""
    try:
        from app.db.session import async_session
        from app.services.error_log_service import log_error
        tb_str = "".join(tb_parts)[:8000] if tb_parts else ""
        async with async_session() as db:
            await log_error(db, message, "ERROR", path=source, source=source, traceback_str=tb_str)
    except Exception as e:
        logger.debug("Error logging to DB failed: %s", e)


def _asyncio_exception_handler(loop, context):
    """Log unhandled task exceptions (e.g. from bot polling) to DB and logger."""
    exc = context.get("exception")
    if exc is not None:
        logger.warning("Async task error (bot/background): %s", exc, exc_info=exc)
        try:
            tb_parts = traceback.format_exception(type(exc), exc, exc.__traceback__)
            asyncio.create_task(_log_async_error(str(exc), "async_task", tb_parts))
        except Exception as e:
            logger.debug("Could not schedule error log task: %s", e)
    else:
        logger.warning("Async context: %s", context)


async def _log_error_to_db(
    request: Request,
    exc: Exception,
    status_code: int,
    level: str = "ERROR",
) -> None:
    """Persist error details to DB so they are visible from admin UI."""
    try:
        body_bytes = await request.body()
        body = body_bytes.decode("utf-8", errors="ignore")
    except Exception:
        body = ""

    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[:8000]

    client_ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    extra = {
        "query_params": dict(request.query_params),
        "source": "api",
    }

    # Reuse standard DB dependency to avoid duplicating engine/session creation
    async for db in get_db():
        try:
            log = ErrorLog(
                level=level,
                message=str(exc)[:500],
                path=request.url.path,
                method=request.method,
                status_code=status_code,
                client_ip=client_ip,
                user_agent=ua[:255] if ua else None,
                request_body=body[:4000],
                traceback=tb,
                extra=extra,
            )
            db.add(log)
            await db.commit()
        except Exception as log_exc:
            logger.error("Failed to write error log: %s", log_exc, exc_info=log_exc)
        finally:
            break


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

    # Daily matches + autopost jobs when bot is configured
    if is_bot_configured():
        scheduler.add_job(_daily_matches_job, "cron", hour=12, minute=0, id="daily_matches")
        scheduler.add_job(_autopost_job, "interval", minutes=1, id="autopost")
        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started (daily matches, autopost every 1 min)")

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
app.include_router(errors_router.router, prefix="/api/v1", tags=["errors"])
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
app.include_router(football.router, prefix="/api/v1", tags=["football"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors (422) to DB so they appear in admin."""
    await _log_error_to_db(request, exc, status_code=422, level="WARNING")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    # Логируем все HTTPException (и 4xx, и 5xx), чтобы видеть любые ошибки в админке.
    level = "ERROR" if exc.status_code >= 500 else "WARNING"
    await _log_error_to_db(request, exc, status_code=exc.status_code, level=level)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    await _log_error_to_db(request, exc, status_code=500, level="ERROR")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
