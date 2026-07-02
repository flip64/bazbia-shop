# -*- coding: utf-8 -*-

"""
سرویس‌های ایجاد اطلاعات محصول

تمام عملیات ساخت محصول از طریق این فایل انجام می‌شود.
"""
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import os
import requests

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
  Product.objects.create(
    name=product_data.name,
    slug=product_data.slug,
    description=product_data.description,
    base_price=product_data.price,
    quantity=product_data.quantity,
    category=product_data.category,
  )

def create_variant(product, product_data):
    """
    ایجاد واریانت محصول
    """
    ProductVariant.objects.create(
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
        defaults={"slug": ...}
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
    
