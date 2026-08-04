# -*- coding: utf-8 -*-

from products.models import Product
from products.services.variant_stock import (
    calculate_variant_available_stock,
)


def calculate_product_stock(
    product: Product,
) -> int:
    """
    موجودی قابل عرضه کل یک محصول را محاسبه می‌کند.

    موجودی یک محصول از مجموع موجودی قابل عرضه تمام
    واریانت‌های آن به دست می‌آید.

    موجودی قابل عرضه هر واریانت شامل دو بخش است:

    1. موجودی واقعی انبار بازبیا
       ``ProductVariant.stock``

    2. موجودی معتبر تأمین‌کنندگان خارجی
       ``SupplierOffer.supplier_stock``

    Parameters
    ----------
    product : Product
        محصولی که موجودی قابل عرضه کل آن باید محاسبه شود.

    Returns
    -------
    int
        مجموع موجودی قابل عرضه تمام واریانت‌های محصول.

        اگر محصول هیچ واریانتی نداشته باشد، مقدار صفر
        برگردانده می‌شود.

    Example
    -------
    فرض کنیم یک محصول دو واریانت داشته باشد:

    واریانت اول:
        موجودی داخلی: 3
        موجودی تأمین‌کننده: 20
        موجودی قابل عرضه: 23

    واریانت دوم:
        موجودی داخلی: 2
        موجودی تأمین‌کننده: 5
        موجودی قابل عرضه: 7

    خروجی این تابع برابر 30 خواهد بود.

    Business Rules
    --------------
    - موجودی داخلی و موجودی تأمین‌کننده جدا نگهداری می‌شوند.
    - موجودی تأمین‌کننده جزو دارایی انبار بازبیا نیست.
    - جمع این دو فقط برای تعیین موجودی قابل سفارش استفاده می‌شود.
    - حسابداری انبار فقط از ``ProductVariant.stock`` استفاده می‌کند.

    Notes
    -----
    این تابع هیچ تغییری در دیتابیس ایجاد نمی‌کند.

    محاسبه موجودی هر واریانت به سرویس
    ``calculate_variant_available_stock`` واگذار شده است تا
    منطق موجودی در یک محل مرکزی نگهداری شود.
    """

    total_available_stock = sum(
        calculate_variant_available_stock(variant)
        for variant in product.variants.all()
    )

    return int(total_available_stock)