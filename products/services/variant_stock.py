# -*- coding: utf-8 -*-

from django.db.models import Sum

from products.models import ProductVariant


def calculate_variant_available_stock(
    variant: ProductVariant,
) -> int:
    """
    موجودی قابل عرضه یک واریانت را محاسبه می‌کند.

    تعریف موجودی‌ها
    ----------------
    موجودی داخلی:
        مقدار فیلد ``ProductVariant.stock`` است و فقط نشان‌دهنده
        کالایی است که واقعاً در انبار بازبیا قرار دارد.

    موجودی تأمین‌کنندگان:
        مجموع ``supplier_stock`` پیشنهادهای معتبر و فعال
        تأمین‌کنندگان خارجی است.

    موجودی قابل عرضه:
        مجموع موجودی داخلی بازبیا و موجودی معتبر
        تأمین‌کنندگان خارجی است.

    Parameters
    ----------
    variant : ProductVariant
        واریانتی که موجودی قابل عرضه آن باید محاسبه شود.

    Returns
    -------
    int
        مجموع موجودی داخلی و موجودی معتبر تأمین‌کنندگان.

    Example
    -------
    اگر وضعیت یک واریانت چنین باشد:

        موجودی داخلی بازبیا: 3
        موجودی تأمین‌کننده اول: 20
        موجودی تأمین‌کننده دوم: 5

    خروجی تابع برابر 28 خواهد بود.

    Business Rules
    --------------
    فقط پیشنهادهایی در محاسبه وارد می‌شوند که:

    - تأمین‌کننده آن‌ها فعال باشد.
    - خود پیشنهاد موجود و قابل عرضه باشد.
    - مقدار موجودی تأمین‌کننده بیشتر از صفر باشد.

    Notes
    -----
    این تابع هیچ تغییری در دیتابیس ایجاد نمی‌کند.

    این تابع نباید مقدار ``ProductVariant.stock`` را تغییر دهد؛
    چون آن فیلد فقط متعلق به موجودی داخلی انبار بازبیا است.
    """

    internal_stock = int(variant.stock or 0)

    supplier_stock_result = (
        variant.supplier_offers
        .filter(
            supplier__is_active=True,
            is_available=True,
            supplier_stock__gt=0,
        )
        .aggregate(
            total_stock=Sum("supplier_stock")
        )
    )

    supplier_stock = int(
        supplier_stock_result["total_stock"] or 0
    )

    return internal_stock + supplier_stock