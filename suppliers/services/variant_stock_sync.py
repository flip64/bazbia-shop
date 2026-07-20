
# -*- coding: utf-8 -*-

from core.logging_config import get_logger

from suppliers.models import SupplierOffer
from suppliers.services.offer_sync_policy import (
    can_sync_variant_from_offer,
)





logger = get_logger(__name__)


def sync_variant_stock_from_offer(
    offer: SupplierOffer,
) -> bool:
    """
    موجودی واریانت را از پیشنهاد اصلی تأمین‌کننده
    به‌روزرسانی می‌کند.
    """

    can_sync = can_sync_variant_from_offer(
        offer
    )

    logger.debug(
        "بررسی همگام‌سازی موجودی | "
        "offer_id=%s | "
        "variant_id=%s | "
        "can_sync=%s | "
        "supplier_stock=%s | "
        "variant_stock=%s",
        offer.pk,
        offer.variant_id,
        can_sync,
        offer.supplier_stock,
        offer.variant.stock,
    )

    if not can_sync:
        return False

    variant = offer.variant

    new_stock = (
        offer.supplier_stock
        if offer.is_available
        else 0
    )

    if variant.stock == new_stock:
        logger.debug(
            "موجودی تغییری نکرد | "
            "variant_id=%s | "
            "stock=%s",
            variant.pk,
            variant.stock,
        )
        return False

    old_stock = variant.stock

    variant.stock = new_stock
    variant.save(update_fields=["stock"])

    logger.info(
        "موجودی واریانت به‌روزرسانی شد | "
        "variant_id=%s | "
        "old_stock=%s | "
        "new_stock=%s",
        variant.pk,
        old_stock,
        new_stock,
    )

    return True
