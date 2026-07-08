# -*- coding: utf-8 -*-

import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

BASE_DIR = "/home/bazbiair/bazbia"   # مسیر پروژه

sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")
django.setup()

from suppliers.models import SupplierPriceHistory

since = timezone.now() - timedelta(hours=24)

print("=" * 80)
print("محصولاتی که در 24 ساعت گذشته تغییر قیمت داشته‌اند")
print("=" * 80)

changes = SupplierPriceHistory.objects.filter(
    created_at__gte=since
).select_related(
    "supplier_offer__supplier",
    "supplier_offer__variant__product"
).order_by("-created_at")

if not changes.exists():
    print("هیچ تغییر قیمتی در 24 ساعت گذشته ثبت نشده است.")
else:
    for item in changes:
        previous = (
            SupplierPriceHistory.objects
            .filter(
                supplier_offer=item.supplier_offer,
                created_at__lt=item.created_at
            )
            .order_by("-created_at")
            .first()
        )

        print(f"محصول : {item.supplier_offer.variant.product.name}")
        print(f"تامین کننده : {item.supplier_offer.supplier.name}")
        print(f"قیمت : {previous.price if previous else '-'} ➜ {item.price}")
        print(f"زمان : {item.created_at}")
        print("-" * 80)

print("\n")
print("=" * 80)
print("آخرین تغییر قیمت")
print("=" * 80)

last = SupplierPriceHistory.objects.select_related(
    "supplier_offer__supplier",
    "supplier_offer__variant__product"
).order_by("-created_at").first()

if last:
    previous = (
        SupplierPriceHistory.objects
        .filter(
            supplier_offer=last.supplier_offer,
            created_at__lt=last.created_at
        )
        .order_by("-created_at")
        .first()
    )

    print(f"محصول : {last.supplier_offer.variant.product.name}")
    print(f"SKU : {last.supplier_offer.variant.sku}")
    print(f"تامین کننده : {last.supplier_offer.supplier.name}")
    print(f"قیمت : {previous.price if previous else '-'} ➜ {last.price}")
    print(f"زمان : {last.created_at}")
else:
    print("هیچ تغییر قیمتی ثبت نشده است.")
