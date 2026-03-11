from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.product import Product
from app.db.models.app_config import AppConfig
from app.db.models.post import Post
from app.api.deps import get_admin_user
from app.schemas.post import PostCreate, PostResponse, PostListResponse
from app.bot.bot import get_bot, is_bot_configured
from app.services.post_service import send_post_to_channel, _build_product_deeplink, _build_shop_deeplink

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads"
POSTS_UPLOADS = UPLOADS_DIR / "posts"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


async def _get_channel_id(db: AsyncSession) -> str | None:
    """Get channel_id from AppConfig or settings."""
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    channel = getattr(config, "channel_id", None) if config else None
    if channel and str(channel).strip():
        return str(channel).strip()
    return getattr(settings, "channel_id", None) or None


def _fill_post_from_product(post_data: dict, product: Product) -> dict:
    """Auto-fill photo_url, button_text, button_url from product when not set."""
    data = dict(post_data)
    if not product:
        return data

    if not data.get("photo_url"):
        image_url = None
        if product.media:
            for m in sorted(product.media, key=lambda x: x.sort_order):
                if m.media_type == "image":
                    image_url = m.file_path
                    break
        if not image_url and product.image_url:
            image_url = product.image_url
        if image_url:
            if image_url.startswith("http"):
                data["photo_url"] = image_url
            else:
                from urllib.parse import urlparse
                base = getattr(settings, "public_base_url", "").strip()
                if not base:
                    parsed = urlparse(settings.webapp_url)
                    base = f"{parsed.scheme}://{parsed.netloc}"
                data["photo_url"] = base.rstrip("/") + ("/" + image_url.lstrip("/"))

    if not data.get("button_text"):
        data["button_text"] = "Перейти к товару"

    if not data.get("button_url") and product.id:
        data["button_url"] = _build_product_deeplink(product.id)

    return data


@router.get("/posts", response_model=PostListResponse)
async def admin_list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """List posts with pagination, sorted by created_at desc."""
    count_stmt = select(func.count(Post.id))
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(Post)
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    posts = result.scalars().all()

    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in posts],
        total=total,
    )


@router.post("/posts", response_model=PostResponse)
async def admin_create_post(
    data: PostCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Create a draft post. Auto-fills photo/button from product when product_id is set."""
    payload = data.model_dump(exclude_unset=True)
    product = None
    if data.product_id:
        res = await db.execute(
            select(Product).where(Product.id == data.product_id).options(selectinload(Product.media))
        )
        product = res.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=400, detail="Product not found")

    payload = _fill_post_from_product(payload, product)
    post = Post(**payload)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return PostResponse.model_validate(post)


@router.get("/posts/{post_id}", response_model=PostResponse)
async def admin_get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Get a single post."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse.model_validate(post)


@router.post("/posts/{post_id}/send")
async def admin_send_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """Send post to the configured Telegram channel."""
    if not is_bot_configured():
        raise HTTPException(status_code=400, detail="Bot not configured — posts unavailable")
    if not get_bot():
        raise HTTPException(status_code=400, detail="Bot not initialized")

    channel_id = await _get_channel_id(db)
    if not channel_id:
        raise HTTPException(status_code=400, detail="Channel not configured. Set channel_id in Settings → Main.")

    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.sent_at:
        raise HTTPException(status_code=400, detail="Post already sent")

    text = (post.text or "").strip() or "(пусто)"
    button_text = (post.button_text or "").strip() or None
    button_url = (post.button_url or "").strip() or None
    if not button_url and post.product_id:
        button_url = _build_product_deeplink(post.product_id)
    if not button_url:
        button_url = _build_shop_deeplink()
    if not button_text:
        button_text = "Открыть магазин"

    try:
        message_id = await send_post_to_channel(
            channel_id=channel_id,
            text=text,
            photo_url=post.photo_url,
            photo_file_id=post.photo_file_id,
            button_text=button_text,
            button_url=button_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to send post to channel: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to send: {e}")

    post.sent_at = func.now()
    post.message_id = message_id
    post.channel_id = channel_id
    await db.commit()
    await db.refresh(post)

    return {
        "ok": True,
        "message_id": message_id,
        "channel_id": channel_id,
    }


@router.post("/posts/upload-image")
async def admin_upload_post_image(
    file: UploadFile = File(...),
    admin: User = Depends(get_admin_user),
):
    """Upload an image for post. Returns URL path."""
    if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    ext = ".jpg"
    if file.content_type == "image/png":
        ext = ".png"
    elif file.content_type == "image/webp":
        ext = ".webp"
    elif file.content_type == "image/gif":
        ext = ".gif"

    POSTS_UPLOADS.mkdir(parents=True, exist_ok=True)
    import uuid
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = POSTS_UPLOADS / filename
    with open(file_path, "wb") as f:
        f.write(content)
    url = f"/uploads/posts/{filename}"
    return {"url": url}
