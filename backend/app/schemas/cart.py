from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.product import ProductResponse


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    modification_type_id: Optional[int] = None
    modification_value: Optional[str] = None


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: ProductResponse
    modification_type_id: Optional[int] = None
    modification_value: Optional[str] = None
    modification_label: Optional[str] = None

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_price: float
    total_items: int





