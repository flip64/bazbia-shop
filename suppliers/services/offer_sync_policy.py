# -*- coding: utf-8 -*-

from suppliers.models import SupplierOffer


def can_sync_variant_from_offer(
    offer: SupplierOffer,
) -> bool:
    """
    مشخص می‌کند آیا این پیشنهاد تأمین‌کننده اجازه دارد
    قیمت و موجودی ProductVariant را به‌روزرسانی کند یا نه.

    سیاست فعلی
    ----------
    در حال حاضر تمام SupplierOfferها مجاز هستند.

    سیاست آینده
    ------------
    بعداً می‌توان این تابع را بر اساس قواعد زیر توسعه داد:

    - اصلی بودن پیشنهاد با is_primary
    - فعال بودن تأمین‌کننده
    - موجود بودن کالا
    - اولویت تأمین‌کننده
    - ارزان‌ترین قیمت خرید
    - زمان آخرین بررسی
    - انتخاب خودکار پیشنهاد مرجع

    Parameters
    ----------
    offer : SupplierOffer
        پیشنهاد تأمین‌کننده‌ای که باید بررسی شود.

    Returns
    -------
    bool
        در نسخه فعلی همیشه True برمی‌گرداند.
    """

    return True