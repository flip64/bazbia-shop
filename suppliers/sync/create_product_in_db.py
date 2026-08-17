# -*- coding: utf-8 -*-

from django.db import transaction

from products.services.product_creator import (
    create_images,
    create_product,
    create_specifications,
    create_tags,
    create_variant,
)
from suppliers.services.get_supplier import get_supplier
from suppliers.services.offer_creator import (
    create_price_history,
    create_supplier_offer,
)
from suppliers.services.variant_price_sync import (
    sync_variant_price_from_offer,
)
from suppliers.services.variant_stock_sync import (
    sync_variant_stock_from_offer,
)


@transaction.atomic
def create_product_from_productData(data):
    """
    محصول، واریانت و پیشنهاد تأمین‌کننده را ایجاد می‌کند
    و سپس قیمت و موجودی فروشگاه را با Offer هماهنگ می‌کند.
    """

    product = create_product(data)

    variant = create_variant(product, data)

    create_specifications(product, data)
    create_tags(product, data)
    create_images(product, data)

    supplier = get_supplier(data.supplier)

    offer = create_supplier_offer(
        supplier=supplier,
        variant=variant,
        supplier_url=data.supplier_url,
        purchase_price=data.price,
        supplier_stock=data.quantity,
        supplier_product_name=data.name,
    )

    create_price_history(offer, data.price)

    sync_variant_price_from_offer(offer)
    sync_variant_stock_from_offer(offer)

    return product