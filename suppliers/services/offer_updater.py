# suppliers/services/offer_updater.py

from suppliers.models import SupplierOffer

def update_supplier_offer(
    *,
    offer: SupplierOffer,
    update_fields: list[str],
) -> SupplierOffer:
    """
    SupplierOffer تغییر‌یافته را در دیتابیس ذخیره می‌کند.

    این سرویس تغییرات را تشخیص نمی‌دهد و تاریخچه ثبت نمی‌کند.
    """

    if not update_fields:
        return offer

    offer.save(update_fields=update_fields)

    return offer