# basalam_integration/services/stock_service.py

from django.conf import settings

from products.services.variant_stock import (
    calculate_variant_available_stock,
)


def calculate_variant_basalam_stock(variant) -> int:
    """
    محاسبه موجودی قابل نمایش در باسلام.

    موجودی بازبیا:
        انبار داخلی + موجودی فعال تأمین‌کنندگان

    سپس بافر ایمنی کم شده و سقف موجودی باسلام
    اعمال می‌شود.
    """

    available_stock = int(
        calculate_variant_available_stock(
            variant
        )
        or 0
    )

    safety_buffer = max(
        int(settings.BASALAM_STOCK_SAFETY_BUFFER),
        0,
    )

    stock_cap = int(
        settings.BASALAM_STOCK_CAP
    )

    basalam_stock = max(
        available_stock - safety_buffer,
        0,
    )

    if stock_cap > 0:
        basalam_stock = min(
            basalam_stock,
            stock_cap,
        )

    return basalam_stock
