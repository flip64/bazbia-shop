# -*- coding: utf-8 -*-

from django.db.models import Sum

from products.models import Product


def calculate_product_stock(product: Product) -> int:
    """
    موجودی کل یک محصول را از مجموع موجودی واریانت‌های آن محاسبه می‌کند.

    Parameters
    ----------
    product : Product
        محصولی که موجودی کل آن باید محاسبه شود.

    Returns
    -------
    int
        مجموع فیلد stock تمام واریانت‌های محصول.

        اگر محصول هیچ واریانتی نداشته باشد، مقدار صفر
        برگردانده می‌شود.

    Examples
    --------
    اگر محصول سه واریانت با موجودی‌های زیر داشته باشد:

        10، 5 و 2

    خروجی تابع برابر 17 خواهد بود.

    Notes
    -----
    این تابع هیچ تغییری در دیتابیس ایجاد نمی‌کند.
    فقط موجودی واریانت‌ها را می‌خواند و مجموع آن‌ها را برمی‌گرداند.
    """

    result = product.variants.aggregate(
        total_stock=Sum("stock")
    )

    return result["total_stock"] or 0
