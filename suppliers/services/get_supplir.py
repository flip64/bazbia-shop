from suppliers.models import Supplier


def get_supplier(name):
    """
    دریافت تأمین‌کننده بر اساس نام.

    اگر وجود نداشته باشد None برمی‌گرداند.
    """

    try:
        return Supplier.objects.get(name=name)
    except Supplier.DoesNotExist:
        return None
