from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.banner import Banner
from app.schemas.banner import BannerResponse

router = APIRouter()


@router.get("/banners", response_model=List[BannerResponse])
async def get_banners(db: AsyncSession = Depends(get_db)):
    """List active banners for catalog, ordered by sort_order."""
    result = await db.execute(
        select(Banner)
        .where(Banner.is_active == True)
        .order_by(Banner.sort_order, Banner.id)
    )
    return [BannerResponse.model_validate(b) for b in result.scalars().all()]
