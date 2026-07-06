# -*- coding: utf-8 -*-

from product_data import ProductData


def product_from_json(data):
    """
    تبدیل dict به ProductData
    """

    product = ProductData()

    product.name = data.get("name")
    product.slug = data.get("slug")
    product.description = data.get("description", "")
    product.category = data.get("category")

    product.price = data.get("price", 0)
    product.quantity = data.get("quantity", 0)

    product.images = data.get("images", [])
    product.videos = data.get("videos", [])

    product.specifications = data.get("specifications", [])
    product.attributes = data.get("attributes", [])
    product.tags = data.get("tags", [])

    product.supplier = data.get("supplier")
    product.supplier_url = data.get("supplier_url")
    product.supplier_product_code = data.get("supplier_product_code")

    product.is_active = data.get("is_active", True)

    product.brand = data.get("brand")
    product.barcode = data.get("barcode")
    product.weight = data.get("weight")

    return product
