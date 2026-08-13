# -*- coding: utf-8 -*-

from django.utils import timezone

from suppliers.models import SupplierOffer
from suppliers.services.offer_updater import update_supplier_offer

from .helpers import to_decimal, to_stock
from .history import save_price_history


def update_offer(offer: SupplierOffer, item) -> bool:
    """
    تغییرات قیمت و موجودی SupplierOffer را بررسی و اعمال می‌کند.

    وظایف:
    - مقایسه قیمت و موجودی
    - ثبت تاریخچه در صورت تغییر قیمت
    - اعمال تغییرات روی شیء Offer
    - فراخوانی سرویس ذخیره Offer

    خروجی:
    True  اگر قیمت یا موجودی تغییر کرده باشد.
    False اگر قیمت و موجودی تغییری نکرده باشند.
    """

    new_price = to_decimal(item.price)
    new_stock = to_stock(item.quantity)

    price_changed = offer.purchase_price != new_price
    stock_changed = offer.supplier_stock != new_stock

    changed_fields = []

    if price_changed:
        # قبل از تغییر purchase_price اجرا شود
        save_price_history(offer, new_price)

        offer.purchase_price = new_price
        changed_fields.append("purchase_price")

    if stock_changed:
        offer.supplier_stock = new_stock
        changed_fields.append("supplier_stock")

    # چون محصول در اطلاعات جدید تأمین‌کننده دیده شده است
    offer.last_seen = timezone.now()

    changed_fields.extend(
        [
            "last_seen",
            "last_checked",
            "updated_at",
        ]
    )

    update_supplier_offer(
        offer=offer,
        update_fields=changed_fields,
    )

    return price_changed or stock_changed