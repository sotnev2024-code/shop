from app.config import settings, ProductSource
from app.services.product_loader.base import BaseProductLoader
from app.services.product_loader.db_loader import DatabaseLoader
from app.services.product_loader.moysklad import MoySkladLoader
from app.services.product_loader.one_c import OneCLoader


def get_product_loader(**kwargs) -> BaseProductLoader:
    """Factory to get the correct product loader based on config."""
    source = settings.product_source
    if source == ProductSource.MOYSKLAD:
        return MoySkladLoader()
    elif source == ProductSource.ONE_C:
        return OneCLoader()
    else:
        return DatabaseLoader(kwargs.get("db"))





