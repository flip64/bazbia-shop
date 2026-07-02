# -*- coding: utf-8 -*-

"""
سرویس‌های ایجاد اطلاعات محصول

تمام عملیات ساخت محصول از طریق این فایل انجام می‌شود.
"""

import os
import requests

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.utils.text import slugify
from products.services.helpper import create_slug
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
    return Product.objects.create(
        name=product_data.name,
        slug=create_slug(name),
        description=product_data.description,
        base_price=product_data.price,
        quantity=product_data.quantity,
        category=product_data.category,
    )


def create_variant(product, product_data):
    """
    ایجاد واریانت محصول
    """
    return ProductVariant.objects.create(
        product=product,
        sku=product_data.sku,
        price=product_data.price,
        stock=product_data.quantity,
    )


def create_specifications(product, product_data):
    """
    ایجاد مشخصات محصول
    """
    for spec in product_data.specifications:
        ProductSpecification.objects.create(
            product=product,
            name=spec["name"],
            value=spec["value"],
        )


def create_tags(product, product_data):
    """
    ایجاد تگ‌های محصول
    """
    for tag_name in product_data.tags:
        tag, _ = Tag.objects.get_or_create(
            name=tag_name,
            defaults={
                "slug": slugify(tag_name),
            },
        )
        product.tags.add(tag)


def create_images(product, product_data):
    """
    ایجاد تصاویر محصول
    """
    for url in product_data.images:
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()

            temp = NamedTemporaryFile(delete=True)
            temp.write(response.content)
            temp.flush()

            filename = os.path.basename(url.split("?")[0])

            image = ProductImage(
                product=product,
                source_url=url,
            )

            image.image.save(filename, File(temp), save=True)

        except Exception as e:
            print(f"خطا در دانلود تصویر {url}: {e}")


def create_videos(product, product_data):
    """
    ایجاد ویدئوهای محصول
    """
    pass
