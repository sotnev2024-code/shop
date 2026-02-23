"""
Delivery service integrations.
Placeholder for future delivery API integrations (CDEK, Russian Post, Boxberry, DPD).
"""

from __future__ import annotations

from typing import Any


class DeliveryService:
    """Base delivery service."""

    SERVICES = {
        "cdek": "СДЭК",
        "russian_post": "Почта России",
        "boxberry": "Boxberry",
        "dpd": "DPD",
    }

    @staticmethod
    async def get_available_services() -> list[dict[str, Any]]:
        """Get list of available delivery services."""
        return [
            {"id": key, "name": name}
            for key, name in DeliveryService.SERVICES.items()
        ]

    @staticmethod
    async def calculate_cost(
        service_id: str,
        from_city: str,
        to_city: str,
        weight: float,
    ) -> dict[str, Any]:
        """Calculate delivery cost. Placeholder for actual API integration."""
        # TODO: Implement actual API calls
        return {
            "service": service_id,
            "cost": 0,
            "days": "3-5",
            "message": "Расчёт недоступен",
        }

    @staticmethod
    async def create_shipment(
        service_id: str,
        order_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a shipment. Placeholder for actual API integration."""
        # TODO: Implement actual API calls
        return {
            "tracking_number": None,
            "message": "Создание отправления недоступно",
        }





