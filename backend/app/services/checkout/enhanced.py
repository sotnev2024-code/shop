from typing import Any

from app.services.checkout.base import BaseCheckout


class EnhancedCheckout(BaseCheckout):
    """Enhanced checkout: name, phone, address via Yandex Maps."""

    def get_required_fields(self) -> list[str]:
        return ["customer_name", "customer_phone", "address", "address_coords"]

    async def process(self, order_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "customer_name": order_data["customer_name"],
            "customer_phone": order_data["customer_phone"],
            "address": order_data.get("address", ""),
            "address_coords": order_data.get("address_coords"),
        }





