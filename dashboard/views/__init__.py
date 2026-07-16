# -*- coding: utf-8 -*-

from .home import dashboard_home
from .imports import import_dashboard
from .logs import operation_logs
from .price_history import offer_price_history, price_history_list
from .products import (
    product_detail,
    product_list,
    product_price_manager,
    product_profit_manager,
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
    "product_edit",
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
]
