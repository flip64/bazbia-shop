
import os
import sys

import django

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "bazbia_shop.settings",
)

django.setup()


from suppliers.fetchers.pakhshabdi.adaptor_abdi import list_product
from suppliers.logger import info
from suppliers.sync.create_product_in_db import (
    create_product_from_productData,
)
from suppliers.sync.find_offer import find_offer
from suppliers.sync.updater import update_offer


def import_products():
    products = list_product()

    for item in products:
        offer = find_offer(item)

        if offer:
            updated = update_offer(
                offer=offer,
                item=item,
            )

            if updated:
                info(f"{item.name} update shod")
            else:
                info(f"{item.name} taghir nakardeh")

        else:
            create_product_from_productData(item)
            info(f"{item.name} ezafeh shod")


if __name__ == "__main__":
    import_products()
