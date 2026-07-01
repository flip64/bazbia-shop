# -*- coding: utf-8 -*-

"""
سرویس‌های ایجاد اطلاعات محصول

تمام عملیات ساخت محصول از طریق این فایل انجام می‌شود.
"""

from products.models import (
    Product,
    ProductVariant,
    ProductSpecification,
    ProductImage,
    ProductVideo,
    Tag,
)


def create_product(product_data):
    """
    ایجاد محصول
    """
    raise NotImplementedError


def create_variant(product, product_data):
    """
    ایجاد واریانت محصول
    """
    raise NotImplementedError


def create_specifications(product, product_data):
    """
    ایجاد مشخصات محصول
    """
    raise NotImplementedError


def create_tags(product, product_data):
    """
    ایجاد تگ‌های محصول
    """
    raise NotImplementedError


def create_images(product, product_data):
    """
    ایجاد تصاویر محصول
    """
    raise NotImplementedError


def create_videos(product, product_data):
    """
    ایجاد ویدئوهای محصول
    """
    raise NotImplementedError
