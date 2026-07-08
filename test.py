# -*- coding: utf-8 -*-

import os
import sys
import django

BASE_DIR = "/home/bazbiair/bazbia"   # مسیر پروژه خودت

sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")
django.setup()

from suppliers.models import SupplierPriceHistory


def show_last_price_change():
    last = SupplierPriceHistory.objects.order_by("-created_at").first()

    if not last:
        print("هیچ تغییر قیمتی ثبت نشده است.")
        return

    previous = (
        SupplierPriceHistory.objects
        .filter(
            supplier_offer=last.supplier_offer,
            created_at__lt=last.created_at
        )
        .order_by("-created_at")
        .first()
    )

    offer = last.supplier_offer
    variant = offer.variant
    product = variant.product
    supplier = offer.supplier

    print("=" * 60)
    print("آخرین تغییر قیمت")
    print("=" * 60)
    print(f"محصول       : {product.name}")
    print(f"SKU         : {variant.sku}")
    print(f"تامین کننده : {supplier.name}")
    print(f"قیمت قبلی   : {previous.price if previous else 'ندارد'}")
    print(f"قیمت جدید   : {last.price}")
    print(f"زمان تغییر  : {last.created_at}")
    print("=" * 60)


if __name__ == "__main__":
    show_last_price_change()
