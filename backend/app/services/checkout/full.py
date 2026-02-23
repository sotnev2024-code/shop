from typing import Any

from app.services.checkout.base import BaseCheckout


class FullCheckout(BaseCheckout):
    """Full checkout: name, phone, Yandex Maps, payment, delivery service selection."""

    def get_required_fields(self) -> list[str]:
        return [
            "customer_name",
            "customer_phone",
            "address",
            "address_coords",
            "delivery_service",
        ]

    async def process(self, order_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "customer_name": order_data["customer_name"],
            "customer_phone": order_data["customer_phone"],
            "address": order_data.get("address", ""),
            "address_coords": order_data.get("address_coords"),
            "delivery_service": order_data.get("delivery_service"),
            "requires_payment": True,
        }





