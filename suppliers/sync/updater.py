# -*- coding: utf-8 -*-

from django.utils import timezone

from suppliers.models import SupplierOffer
from suppliers.services.offer_updater import update_supplier_offer
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
    اطلاعات جدید تأمین‌کننده را با SupplierOffer مقایسه و
    تغییرات قیمت و موجودی را اعمال می‌کند.

    روند اجرا
    ---------
    1. تبدیل قیمت و موجودی ورودی به نوع استاندارد.
    2. تشخیص تغییر قیمت خرید و موجودی تأمین‌کننده.
    3. ثبت تاریخچه در صورت تغییر قیمت خرید.
    4. ذخیره تغییرات SupplierOffer.
    5. هماهنگ‌سازی قیمت ProductVariant در صورت تغییر قیمت.
    6. هماهنگ‌سازی موجودی ProductVariant در صورت تغییر موجودی.

    Parameters
    ----------
    offer : SupplierOffer
        پیشنهاد موجود تأمین‌کننده که باید به‌روزرسانی شود.

    item
        اطلاعات استانداردشده محصول تأمین‌کننده.
        انتظار می‌رود دارای ویژگی‌های price و quantity باشد.

    Returns
    -------
    bool
        True اگر قیمت یا موجودی تغییر کرده باشد.
        False اگر قیمت و موجودی بدون تغییر باشند.

    Notes
    -----
    حتی اگر قیمت و موجودی تغییر نکرده باشند، زمان آخرین مشاهده
    و آخرین بررسی SupplierOffer ذخیره می‌شود.
    """

    new_price = to_decimal(item.price)
    new_stock = to_stock(item.quantity)

    price_changed = offer.purchase_price != new_price
    stock_changed = offer.supplier_stock != new_stock

    changed_fields = []

    if price_changed:
        # تاریخچه باید قبل از تغییر purchase_price ثبت شود.
        save_price_history(
            offer=offer,
            new_price=new_price,
        )

        offer.purchase_price = new_price
        changed_fields.append("purchase_price")

    if stock_changed:
        offer.supplier_stock = new_stock
        changed_fields.append("supplier_stock")

    checked_at = timezone.now()

    # محصول در آخرین اطلاعات تأمین‌کننده مشاهده شده است.
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

    # فقط زمانی که قیمت خرید تغییر کرده باشد،
    # قیمت فروش واریانت دوباره محاسبه می‌شود.
    if price_changed:
        sync_variant_price_from_offer(offer)

    # فقط زمانی که موجودی تأمین‌کننده تغییر کرده باشد،
    # موجودی واریانت هماهنگ می‌شود.
    if stock_changed:
        sync_variant_stock_from_offer(offer)

    return price_changed or stock_changed