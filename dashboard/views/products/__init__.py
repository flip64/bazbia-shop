# -*- coding: utf-8 -*-

from .list import (
    product_list,
    product_price_manager,
    product_profit_manager,
)

from .detail import product_detail

from .edit import product_info_edit


__all__ = [
    "product_list",
    "product_detail",
    "product_info_edit",
    "product_price_manager",
    "product_profit_manager",
]
