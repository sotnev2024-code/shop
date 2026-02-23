from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BannerResponse(BaseModel):
    id: int
    image_url: str
    link: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BannerCreate(BaseModel):
    image_url: str
    link: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class BannerUpdate(BaseModel):
    image_url: Optional[str] = None
    link: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
