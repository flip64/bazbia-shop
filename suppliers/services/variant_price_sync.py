# -*- coding: utf-8 -*-

"""
همگام‌سازی قیمت واریانت از روی پیشنهاد تأمین‌کننده.

وظایف این ماژول
---------------
1. محاسبه قیمت فروش از روی قیمت خرید و درصد سود.
2. گرد کردن قیمت به نزدیک‌ترین ۱۰۰۰ ریال.
3. به‌روزرسانی قیمت واریانت در صورت مجاز بودن همگام‌سازی.
"""

from decimal import Decimal, ROUND_HALF_UP

from suppliers.models import SupplierOffer
from suppliers.services.offer_sync_policy import (
    can_sync_variant_from_offer,
)

# ثابت‌های مالی
ONE = Decimal("1")
HUNDRED = Decimal("100")
ROUND_TO = Decimal("1000")


def to_decimal(value) -> Decimal:
    """
    مقدار ورودی را به Decimal تبدیل می‌کند.

    از تبدیل توسط str استفاده می‌شود تا خطاهای float
    وارد محاسبات مالی نشوند.

    Parameters
    ----------
    value : Decimal | int | float | str

    Returns
    -------
    Decimal
    """

    if isinstance(value, Decimal):
        return value

    return Decimal(str(value))


def calculate_sale_price(
    purchase_price,
    profit_percent,
) -> Decimal:
    """
    قیمت فروش را محاسبه می‌کند.

    فرمول:

        sale_price = purchase_price × (1 + profit_percent / 100)

    سپس نتیجه به نزدیک‌ترین ۱۰۰۰ ریال گرد می‌شود.

    Parameters
    ----------
    purchase_price
        قیمت خرید تأمین‌کننده.

    profit_percent
        درصد سود.

    Returns
    -------
    Decimal
        قیمت فروش گرد شده.
    """

    purchase_price = to_decimal(purchase_price)
    profit_percent = to_decimal(profit_percent)

    sale_price = purchase_price * (
        ONE + profit_percent / HUNDRED
    )

    return sale_price.quantize(
        ROUND_TO,
        rounding=ROUND_HALF_UP,
    )


def sync_variant_price_from_offer(
    offer: SupplierOffer,
) -> bool:
    """
    قیمت فروش واریانت را از روی پیشنهاد تأمین‌کننده
    به‌روزرسانی می‌کند.

    در صورتی که:
        - همگام‌سازی مجاز نباشد
        - یا قیمت تغییری نکند

    مقدار False برمی‌گرداند.

    Returns
    -------
    bool
        True اگر قیمت تغییر کرده باشد.
        False اگر تغییری انجام نشده باشد.
    """

    if not can_sync_variant_from_offer(offer):
        return False

    variant = offer.variant

    new_price = calculate_sale_price(
        purchase_price=offer.purchase_price,
        profit_percent=variant.profit_percent,
    )

    if variant.price == new_price:
        return False

    variant.price = new_price

    variant.save(
        update_fields=["price"],
    )

    return True
