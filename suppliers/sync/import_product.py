# -*- coding: utf-8 -*-

import os
import sys

import django


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "bazbia_shop.settings",
)

django.setup()


from core.logging_config import get_logger
from core.sync_tracker import SyncRun

from suppliers.fetchers.pakhshabdi.adaptor_abdi import (
    list_product,
)
from suppliers.sync.create_product_in_db import (
    create_product_from_productData,
)
from suppliers.sync.find_offer import find_offer
from suppliers.sync.updater import update_offer


logger = get_logger(__name__)


def import_products():
    with SyncRun(
        name="import_products",
        supplier="abdi",
    ) as sync:

        products = list_product()

        sync.stats.received = len(products)

        logger.info(
            "محصولات تأمین‌کننده دریافت شدند | count=%s",
            len(products),
        )

        for item in products:
            try:
                offer = find_offer(item)

                if offer:
                    updated = update_offer(
                        offer=offer,
                        item=item,
                    )

                    if updated:
                        sync.stats.updated += 1

                        logger.info(
                            "پیشنهاد تأمین‌کننده به‌روزرسانی شد | "
                            "product=%s | "
                            "offer_id=%s | "
                            "variant_id=%s | "
                            "supplier_url=%s",
                            item.name,
                            offer.id,
                            offer.variant_id,
                            item.supplier_url,
                        )

                    else:
                        sync.stats.unchanged += 1

                        logger.debug(
                            "محصول تغییری نکرده است | "
                            "product=%s | "
                            "offer_id=%s",
                            item.name,
                            offer.id,
                        )

                else:
                    product = create_product_from_productData(
                        item
                    )

                    sync.stats.created += 1

                    logger.info(
                        "محصول جدید ایجاد شد | "
                        "product=%s | "
                        "product_id=%s | "
                        "supplier_url=%s",
                        item.name,
                        getattr(product, "id", None),
                        item.supplier_url,
                    )

            except Exception:
                sync.stats.failed += 1

                logger.exception(
                    "خطا در پردازش محصول | "
                    "product=%s | "
                    "supplier_url=%s",
                    getattr(item, "name", "-"),
                    getattr(item, "supplier_url", "-"),
                )


if __name__ == "__main__":
    import_products()
