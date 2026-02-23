from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PromoCodeCreate(BaseModel):
    code: str
    discount_type: str  # percent | fixed | free_delivery
    discount_value: float = 0
    min_order_amount: float = 0
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True
    first_order_only: bool = False


class PromoCodeResponse(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: float
    min_order_amount: float
    max_uses: Optional[int] = None
    used_count: int
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool
    first_order_only: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class PromoCodeCheck(BaseModel):
    code: str
    cart_total: Optional[float] = None
    delivery_type: Optional[str] = None


class PromoCodeCheckResponse(BaseModel):
    valid: bool
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    message: str = ""





