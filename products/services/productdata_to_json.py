# -*- coding: utf-8 -*-

def product_to_json(product):
    """
    تبدیل ProductData به dict قابل تبدیل به JSON
    """

    return {
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "category": product.category,

        "price": product.price,
        "quantity": product.quantity,

        "images": product.images,
        "videos": product.videos,

        "specifications": product.specifications,
        "attributes": product.attributes,
        "tags": product.tags,

        "supplier": product.supplier,
        "supplier_url": product.url,
        "supplier_product_code": product.supplier_product_code,

        "is_active": product.is_active,

        "brand": product.brand,
        "barcode": product.barcode,
        "weight": product.weight,
    }
