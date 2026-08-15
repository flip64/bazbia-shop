# -*- coding: utf-8 -*-

from .detail import product_detail

from .edit import (
    product_images_edit,
    product_info_edit,
    product_specifications_edit,
    product_tags_edit,
)



    

from .list import (
    product_list,
    product_price_manager,
    product_profit_manager,
)

__all__ = [
    "product_list",
    "product_detail",
    "product_info_edit",
    "product_images_edit",
    "product_specifications_edit",
    "product_tags_edit",
    "product_price_manager",
    "product_profit_manager",
]