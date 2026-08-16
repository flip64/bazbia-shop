# suppliers/services/variant_price_sync.py

from decimal import Decimal, ROUND_HALF_UP

from suppliers.models import SupplierOffer


def calculate_sale_price(
    purchase_price: Decimal,
    profit_percent: Decimal,
) -> Decimal:
    """
    محاسبه قیمت فروش با استفاده از قیمت خرید و درصد سود.
    """

    sale_price = purchase_price * (
        Decimal("1") + profit_percent / Decimal("100")
    )

    return sale_price.quantize(
        Decimal("100"),
        rounding=ROUND_HALF_UP,
    )


def sync_variant_price_from_offer(
    offer: SupplierOffer,
) -> bool:
    """
    قیمت فروش واریانت را از پیشنهاد اصلی تأمین‌کننده
    به‌روزرسانی می‌کند.
    """

    if not offer.is_primary:
        return False

    variant = offer.variant

    new_price = calculate_sale_price(
        purchase_price=offer.purchase_price,
        profit_percent=variant.profit_percent,
    )

    if variant.price == new_price:
        return False

    variant.price = new_price
    variant.save(update_fields=["price"])

    return True