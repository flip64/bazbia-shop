# -*- coding: utf-8 -*-

from django.utils import timezone

from suppliers.models import SupplierOffer

from .helpers import (
    normalize_url,
    to_decimal,
    to_stock,
    is_available,
)

from .history import save_price_history


def find_offer(supplier, url):
    """
    جستجوی پیشنهاد تأمین‌کننده بر اساس لینک محصول
    """

    url = normalize_url(url)

    return SupplierOffer.objects.filter(
        supplier=supplier,
        supplier_url=url
    ).select_related("variant").first()


def update_offer(offer, item):
    """
    بروزرسانی اطلاعات SupplierOffer
    """

    price = to_decimal(item["price"])
    stock = to_stock(item["stock"])

    # ثبت تاریخچه قیمت
    save_price_history(offer, price)

    offer.purchase_price = price
    offer.supplier_stock = stock
    offer.is_available = is_available(stock)
    offer.last_seen = timezone.now()

    offer.save(
        update_fields=[
            "purchase_price",
            "supplier_stock",
            "is_available",
            "last_seen",
            "last_checked",
            "updated_at",
        ]
    )

    return offer


def update_existing_product(supplier, item):
    """
    اگر محصول وجود داشت بروزرسانی می‌شود.
    در غیر این صورت None برمی‌گرداند.
    """

    offer = find_offer(
        supplier,
        item["url"]
    )

    if not offer:
        return None

    return update_offer(
        offer,
        item
    )
