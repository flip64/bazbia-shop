# -*- coding: utf-8 -*-

from django.utils import timezone

from suppliers.models import SupplierOffer
from suppliers.services.offer_updater import (
    update_supplier_offer,
)
from suppliers.services.variant_price_sync import (
    sync_variant_price_from_offer,
)
from suppliers.services.variant_stock_sync import (
    sync_variant_stock_from_offer,
)

from .helpers import to_decimal, to_stock
from .history import save_price_history


def update_offer(
    offer: SupplierOffer,
    item,
) -> bool:
    """
    اطلاعات جدید تأمین‌کننده را با SupplierOffer مقایسه می‌کند،
    تغییرات را ذخیره می‌کند و واریانت مرتبط را همگام می‌سازد.
    """

    new_price = to_decimal(item.price)
    new_stock = to_stock(item.quantity)

    price_changed = (
        offer.purchase_price != new_price
    )

    stock_changed = (
        offer.supplier_stock != new_stock
    )

    changed_fields = []

    if price_changed:
        # تاریخچه باید قبل از تغییر purchase_price ثبت شود.
        save_price_history(
            offer=offer,
            new_price=new_price,
        )

        offer.purchase_price = new_price
        changed_fields.append(
            "purchase_price"
        )

    if stock_changed:
        offer.supplier_stock = new_stock
        changed_fields.append(
            "supplier_stock"
        )

    checked_at = timezone.now()

    offer.last_seen = checked_at
    offer.last_checked = checked_at

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

    # قیمت فروش فقط در صورت تغییر قیمت خرید محاسبه می‌شود.
    if price_changed:
        variant_price_changed = (
            sync_variant_price_from_offer(
                offer
            )
        )
    else:
        variant_price_changed = False

    # موجودی واریانت در هر بار پردازش بررسی می‌شود.
    variant_stock_changed = (
        sync_variant_stock_from_offer(
            offer
        )
    )

    return any(
        [
            price_changed,
            stock_changed,
            variant_price_changed,
            variant_stock_changed,
        ]
    )
