from django.utils import timezone

from suppliers.models import SupplierOffer


def create_supplier_offer(
    supplier,
    variant,
    supplier_url,
    purchase_price,
    supplier_stock,
    supplier_product_name="",
    supplier_product_code="",
    is_primary=False,
):
    """
    ایجاد پیشنهاد تأمین‌کننده برای یک واریانت محصول.

    اگر پیشنهاد قبلاً وجود داشته باشد،
    همان رکورد برگردانده می‌شود.
    """

    supplier_offer, _ = SupplierOffer.objects.get_or_create(
        supplier=supplier,
        variant=variant,
        defaults={
            "supplier_product_name": supplier_product_name,
            "supplier_product_code": supplier_product_code,
            "supplier_url": supplier_url,
            "purchase_price": purchase_price,
            "supplier_stock": supplier_stock,
            "is_available": supplier_stock > 0,
            "is_primary": is_primary,
            "last_seen": timezone.now(),
        },
    )

    return supplier_offer

from suppliers.models import SupplierPriceHistory


def create_price_history(supplier_offer, price):
    """
    ثبت یک رکورد جدید در تاریخچه قیمت تأمین‌کننده.

    Args:
        supplier_offer: شیء SupplierOffer
        price: قیمت خرید 

    Returns:
        SupplierPriceHistory
    """

    history = SupplierPriceHistory.objects.create(
        supplier_offer=supplier_offer,
        price=price,
    )

    return history
