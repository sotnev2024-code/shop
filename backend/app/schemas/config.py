from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AppConfigResponse(BaseModel):
    shop_name: str
    checkout_type: str
    product_source: str
    delivery_enabled: bool
    pickup_enabled: bool
    promo_enabled: bool
    mailing_enabled: bool
    currency: str
    yandex_maps_enabled: bool
    yandex_maps_key: Optional[str] = None
    payment_enabled: bool
    support_link: str = ""
    is_admin: bool = False
    is_owner: bool = False
    bot_photo_url: Optional[str] = None
    bot_username: Optional[str] = None
    store_address: Optional[str] = None
    delivery_city: Optional[str] = None
    delivery_cost: float = 0
    free_delivery_min_amount: float = 0
    min_order_amount_pickup: float = 0
    min_order_amount_delivery: float = 0
    banner_aspect_shape: str = "rectangle"
    banner_size: str = "medium"
    category_image_size: str = "medium"
    # Bonus system
    bonus_enabled: bool = False
    bonus_welcome_enabled: bool = False
    bonus_welcome_amount: float = 0
    bonus_purchase_enabled: bool = False
    bonus_purchase_percent: float = 0
    bonus_spend_enabled: bool = False
    bonus_spend_limit_type: str = "percent"
    bonus_spend_limit_value: float = 0

    model_config = {"from_attributes": True}


class AppConfigAdminUpdate(BaseModel):
    shop_name: Optional[str] = None
    pickup_enabled: Optional[bool] = None
    delivery_enabled: Optional[bool] = None
    currency: Optional[str] = None
    store_address: Optional[str] = None
    delivery_city: Optional[str] = None


class OwnerConfigResponse(BaseModel):
    """Full config visible only to the platform owner."""
    # Modules
    checkout_type: str
    product_source: str
    promo_enabled: bool
    mailing_enabled: bool
    delivery_enabled: bool
    pickup_enabled: bool

    # Delivery services
    delivery_sdek_enabled: bool = False
    delivery_pochta_enabled: bool = False
    delivery_yandex_enabled: bool = False

    # Integration keys (masked for display)
    moysklad_token: Optional[str] = None
    one_c_endpoint: Optional[str] = None
    one_c_login: Optional[str] = None
    one_c_password: Optional[str] = None
    payment_provider_token: Optional[str] = None
    yandex_maps_key: Optional[str] = None
    support_link: Optional[str] = None
    sync_interval_minutes: int = 15

    model_config = {"from_attributes": True}


class OwnerConfigUpdate(BaseModel):
    """Fields the owner can update."""
    checkout_type: Optional[str] = None
    product_source: Optional[str] = None
    promo_enabled: Optional[bool] = None
    mailing_enabled: Optional[bool] = None
    delivery_enabled: Optional[bool] = None
    pickup_enabled: Optional[bool] = None

    # Delivery services
    delivery_sdek_enabled: Optional[bool] = None
    delivery_pochta_enabled: Optional[bool] = None
    delivery_yandex_enabled: Optional[bool] = None

    # Integration keys
    moysklad_token: Optional[str] = None
    one_c_endpoint: Optional[str] = None
    one_c_login: Optional[str] = None
    one_c_password: Optional[str] = None
    payment_provider_token: Optional[str] = None
    yandex_maps_key: Optional[str] = None
    support_link: Optional[str] = None
    sync_interval_minutes: Optional[int] = None

