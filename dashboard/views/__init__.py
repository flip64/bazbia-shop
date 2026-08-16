# -*- coding: utf-8 -*-





from .home import dashboard_home
from .imports import import_dashboard
from .logs import operation_logs
from .price_history import (
    offer_price_history,
    price_history_list,
)

from .products import (
    product_detail,
    product_images_edit,
    product_info_edit,
    product_list,
    product_price_manager,
    product_profit_manager,
    product_specifications_edit,
    product_tags_edit,
    product_variants_edit,
    product_images_edit,
    product_image_delete,
)

from .suppliers import (
    supplier_detail,
    supplier_list,
    supplier_products,
)

from .sync import sync_dashboard


__all__ = [
    "dashboard_home",
    "product_list",
    "product_detail",
    "product_info_edit",
    "product_profit_manager",
    "product_price_manager",
    "supplier_list",
    "supplier_detail",
    "supplier_products",
    "price_history_list",
    "offer_price_history",
    "sync_dashboard",
    "import_dashboard",
    "operation_logs",
    "product_images_edit",
    "product_specifications_edit",
    "product_tags_edit",
    "product_variants_edit",
    "product_images_edit",
    "product_image_delete"

]

