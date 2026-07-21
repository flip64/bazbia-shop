# -*- coding: utf-8 -*-

import logging
from typing import Any

from django.utils import timezone

from suppliers.models import SupplierOffer
from suppliers.services.offer_updater import (
    update_supplier_offer,
)
from suppliers.services.variant_price_sync import (
    sync_variant_price_from_offer,
)
from suppliers.services.variant_stock_sync import (
    sync_variant_stock_from_offer,
)

from .helpers import to_decimal, to_stock
from .history import save_price_history


logger = logging.getLogger(__name__)


def update_offer(
    offer: SupplierOffer,
    item: Any,
) -> bool:
    """
    اطلاعات جدید تأمین‌کننده را با SupplierOffer مقایسه می‌کند.

    عملیات این تابع:

    1. مقایسه قیمت خرید
    2. مقایسه موجودی تأمین‌کننده
    3. ثبت تاریخچه قیمت
    4. ذخیره SupplierOffer
    5. همگام‌سازی قیمت واریانت
    6. همگام‌سازی موجودی واریانت

    خروجی:
        اگر هر بخشی تغییر کرده باشد True برمی‌گرداند.
    """

    offer_id = offer.pk
    variant_id = offer.variant_id
    supplier_id = offer.supplier_id

    supplier_slug = getattr(
        offer.supplier,
        "slug",
        None,
    )

    supplier_url = getattr(
        item,
        "supplier_url",
        None,
    )

    item_name = getattr(
        item,
        "name",
        None,
    )

    logger.debug(
        "شروع بررسی پیشنهاد تأمین‌کننده | "
        "offer_id=%s | variant_id=%s | supplier_id=%s | "
        "supplier=%s | product=%s | supplier_url=%s",
        offer_id,
        variant_id,
        supplier_id,
        supplier_slug,
        item_name,
        supplier_url,
    )

    try:
        new_price = to_decimal(
            item.price
        )

        new_stock = to_stock(
            item.quantity
        )

    except (TypeError, ValueError, AttributeError):

        logger.exception(
            "خطا در تبدیل اطلاعات دریافتی تأمین‌کننده | "
            "offer_id=%s | variant_id=%s | supplier=%s | "
            "product=%s | raw_price=%r | raw_stock=%r",
            offer_id,
            variant_id,
            supplier_slug,
            item_name,
            getattr(item, "price", None),
            getattr(item, "quantity", None),
        )

        raise

    old_price = offer.purchase_price
    old_stock = offer.supplier_stock

    price_changed = (
        old_price != new_price
    )

    stock_changed = (
        old_stock != new_stock
    )

    logger.debug(
        "نتیجه مقایسه پیشنهاد تأمین‌کننده | "
        "offer_id=%s | old_price=%s | new_price=%s | "
        "old_stock=%s | new_stock=%s | "
        "price_changed=%s | stock_changed=%s",
        offer_id,
        old_price,
        new_price,
        old_stock,
        new_stock,
        price_changed,
        stock_changed,
    )

    changed_fields: list[str] = []

    try:
        if price_changed:
            save_price_history(
                offer=offer,
                new_price=new_price,
            )

            offer.purchase_price = new_price

            changed_fields.append(
                "purchase_price"
            )

            logger.info(
                "قیمت خرید پیشنهاد تأمین‌کننده تغییر کرد | "
                "offer_id=%s | variant_id=%s | supplier=%s | "
                "product=%s | old_price=%s | new_price=%s",
                offer_id,
                variant_id,
                supplier_slug,
                item_name,
                old_price,
                new_price,
            )

        if stock_changed:
            offer.supplier_stock = new_stock

            changed_fields.append(
                "supplier_stock"
            )

            logger.info(
                "موجودی پیشنهاد تأمین‌کننده تغییر کرد | "
                "offer_id=%s | variant_id=%s | supplier=%s | "
                "product=%s | old_stock=%s | new_stock=%s",
                offer_id,
                variant_id,
                supplier_slug,
                item_name,
                old_stock,
                new_stock,
            )

        checked_at = timezone.now()

        offer.last_seen = checked_at
        offer.last_checked = checked_at

        changed_fields.extend(
            [
                "last_seen",
                "last_checked",
                "updated_at",
            ]
        )

        update_supplier_offer(
            offer=offer,
            update_fields=changed_fields,
        )

        logger.debug(
            "پیشنهاد تأمین‌کننده ذخیره شد | "
            "offer_id=%s | update_fields=%s",
            offer_id,
            changed_fields,
        )

    except Exception:

        logger.exception(
            "خطا در ذخیره پیشنهاد تأمین‌کننده | "
            "offer_id=%s | variant_id=%s | supplier=%s | "
            "product=%s | changed_fields=%s",
            offer_id,
            variant_id,
            supplier_slug,
            item_name,
            changed_fields,
        )

        raise

    variant_price_changed = False
    variant_stock_changed = False

    try:
        # قیمت فروش فقط وقتی قیمت خرید تغییر کرده باشد
        # دوباره محاسبه می‌شود.
        if price_changed:
            variant_price_changed = (
                sync_variant_price_from_offer(
                    offer
                )
            )

            if variant_price_changed:
                logger.info(
                    "قیمت فروش واریانت همگام شد | "
                    "offer_id=%s | variant_id=%s | supplier=%s | "
                    "product=%s",
                    offer_id,
                    variant_id,
                    supplier_slug,
                    item_name,
                )
            else:
                logger.debug(
                    "قیمت فروش واریانت نیازی به تغییر نداشت | "
                    "offer_id=%s | variant_id=%s",
                    offer_id,
                    variant_id,
                )

        # موجودی واریانت در هر بار پردازش بررسی می‌شود؛
        # چون ممکن است پیشنهاد اصلی تأمین‌کننده تغییر کرده باشد.
        variant_stock_changed = (
            sync_variant_stock_from_offer(
                offer
            )
        )

        if variant_stock_changed:
            logger.info(
                "موجودی واریانت همگام شد | "
                "offer_id=%s | variant_id=%s | supplier=%s | "
                "product=%s",
                offer_id,
                variant_id,
                supplier_slug,
                item_name,
            )
        else:
            logger.debug(
                "موجودی واریانت نیازی به تغییر نداشت | "
                "offer_id=%s | variant_id=%s",
                offer_id,
                variant_id,
            )

    except Exception:

        logger.exception(
            "خطا در همگام‌سازی واریانت | "
            "offer_id=%s | variant_id=%s | supplier=%s | "
            "product=%s | price_changed=%s | stock_changed=%s",
            offer_id,
            variant_id,
            supplier_slug,
            item_name,
            price_changed,
            stock_changed,
        )

        raise

    result = any(
        [
            price_changed,
            stock_changed,
            variant_price_changed,
            variant_stock_changed,
        ]
    )

    if result:
        logger.info(
            "به‌روزرسانی پیشنهاد کامل شد | "
            "offer_id=%s | variant_id=%s | supplier=%s | "
            "product=%s | price_changed=%s | stock_changed=%s | "
            "variant_price_changed=%s | variant_stock_changed=%s",
            offer_id,
            variant_id,
            supplier_slug,
            item_name,
            price_changed,
            stock_changed,
            variant_price_changed,
            variant_stock_changed,
        )
    else:
        logger.debug(
            "پیشنهاد تأمین‌کننده بدون تغییر بود | "
            "offer_id=%s | variant_id=%s | supplier=%s | "
            "product=%s",
            offer_id,
            variant_id,
            supplier_slug,
            item_name,
        )

    return result