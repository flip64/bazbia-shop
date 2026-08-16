# suppliers/services/variant_stock_sync.py

from suppliers.models import SupplierOffer


def sync_variant_stock_from_offer(
    offer: SupplierOffer,
) -> bool:
    """
    موجودی واریانت را از پیشنهاد اصلی تأمین‌کننده
    به‌روزرسانی می‌کند.
    """

    if not offer.is_primary:
        return False

    variant = offer.variant

    new_stock = (
        offer.supplier_stock
        if offer.is_available
        else 0
    )

    if variant.stock == new_stock:
        return False

    variant.stock = new_stock
    variant.save(update_fields=["stock"])

    return True