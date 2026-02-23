from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_order: float
    product_name: str = ""
    modification_type_id: Optional[int] = None
    modification_value: Optional[str] = None
    modification_label: Optional[str] = None

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    address: Optional[str] = None
    address_coords: Optional[dict] = None
    delivery_type: Optional[str] = None
    delivery_service: Optional[str] = None
    promo_code: Optional[str] = None
    bonus_to_use: Optional[float] = None


class OrderResponse(BaseModel):
    id: int
    status: str
    total: float
    discount: float
    bonus_used: float = 0
    delivery_fee: float = 0
    delivery_type: Optional[str] = None
    customer_name: str
    customer_phone: str
    address: Optional[str] = None
    payment_status: Optional[str] = None
    delivery_service: Optional[str] = None
    tracking_number: Optional[str] = None
    created_at: datetime
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int


class OrderStatusUpdate(BaseModel):
    status: str
    tracking_number: Optional[str] = None





