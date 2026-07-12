from suppliers.models import Supplier


def get_supplier(slug):
    """
    دریافت تأمین‌کننده بر اساس نام.

    اگر وجود نداشته باشد None برمی‌گرداند.
    """

    try:
        return Supplier.objects.get(slug=slug)
    except Supplier.DoesNotExist:
        return None
