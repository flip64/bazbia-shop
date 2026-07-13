# -*- coding: utf-8 -*-

from suppliers.models import SupplierPriceHistory

from .helpers import to_decimal


def save_price_history(offer, new_price):
    """
    اگر قیمت تغییر کرده باشد، تاریخچه ثبت می‌شود.

    Parameters
    ----------
    offer : SupplierOffer
    new_price : Decimal | int | str

    Returns
    -------
    bool
        True اگر تاریخچه ثبت شد.
        False اگر قیمت تغییری نکرد.
    """

    new_price = to_decimal(new_price)

    if offer.purchase_price == new_price:
        return False

    SupplierPriceHistory.objects.create(supplier_offer=offer, price=new_price)

    return True
