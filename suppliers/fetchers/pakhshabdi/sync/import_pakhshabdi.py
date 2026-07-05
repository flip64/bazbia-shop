# -*- coding: utf-8 -*-
import os
import sys
import django

# ریشه پروژه
BASE_DIR = "/home/bazbiair/bazbia"
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")
django.setup()

from suppliers.fetchers.pakhshabdi.sync.logger import info, warning, error, exception
from suppliers.fetchers.pakhshabdi.sync.json_loader import load_available_products
from suppliers.fetchers.pakhshabdi.sync.find_offer import find_offer_by_url
from suppliers.fetchers.pakhshabdi.sync.create_product_from_url import create_product_from_url
from suppliers.fetchers.pakhshabdi.sync.updater import update_offer
from suppliers.fetchers.pakhshabdi.get_supplier_abdi import get_supplier_abdi

products = load_available_products()

for item in products:
    supplier = get_supplier_abdi()
    offer = find_offer_by_url(supplier, item["url"])

    if offer:
        if offer.purchase_price == item["price"]:
            info(f"{item['name']} taghir nakardeh")
        else:
            update_offer(offer, item)
            info(f"{item['name']} update shod")
    else:
        create_product_from_url(item["url"])
