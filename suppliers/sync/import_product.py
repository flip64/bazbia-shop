# -*- coding: utf-8 -*-
import os
import sys
import django

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "bazbia_shop.settings"
)

django.setup()

from suppliers.logger import info, warning, error, exception
from suppliers.sync.find_offer import find_offer
from suppliers.sync.updater import update_offer
from suppliers.fetchers.pakhshabdi.adaptor_abdi import list_product
from suppliers.sync.create_product_in_db import create_product_from_productData
products = list_product() 
for item in products:
    supplier = item.supplier
    offer = find_offer(item)
    if offer:
        if offer.purchase_price == item.price:
            info(f"{item.name} taghir nakardeh")
        else:
            update_offer(offer, item)
            info(f"{item.name} update shod")
    else:
        create_product_from_productData(item)
        info(f"{item.name} azageh  shod")



