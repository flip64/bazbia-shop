# torob_integration/services/response_builder.py

import math
from typing import Iterable

from products.models import ProductVariant

from .product_mapper import TorobProductMapper


class TorobResponseBuilder:
    API_VERSION = "torob_api_v3"
    PAGE_SIZE = 100

    @classmethod
    def build_paginated_response(
        cls,
        *,
        variants: Iterable[ProductVariant],
        page: int,
        total: int,
        request=None,
    ) -> dict:
        products = [
            TorobProductMapper.map_variant(
                variant,
                request=request,
            )
            for variant in variants
        ]

        max_pages = max(
            1,
            math.ceil(total / cls.PAGE_SIZE),
        )

        return {
            "api_version": cls.API_VERSION,
            "current_page": int(page),
            "total": int(total),
            "max_pages": int(max_pages),
            "products": products,
        }

    @classmethod
    def build_products_response(
        cls,
        *,
        variants: Iterable[ProductVariant],
        request=None,
    ) -> dict:
        products = [
            TorobProductMapper.map_variant(
                variant,
                request=request,
            )
            for variant in variants
        ]

        total = len(products)

        return {
            "api_version": cls.API_VERSION,
            "current_page": 1,
            "total": total,
            "max_pages": max(1, math.ceil(total / 100)),
            "products": products,
        }

    @classmethod
    def build_empty_response(cls) -> dict:
        return {
            "api_version": cls.API_VERSION,
            "current_page": 1,
            "total": 0,
            "max_pages": 1,
            "products": [],
        }
