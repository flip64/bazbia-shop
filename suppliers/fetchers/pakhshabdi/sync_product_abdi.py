# -*- coding: utf-8 -*-

import os
import sys
import django


BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../")
)

sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")
django.setup()


from suppliers.fetchers.pakhshabdi.json_loader import load_json
from suppliers.fetchers.pakhshabdi.save_json import save_json
from suppliers.fetchers.pakhshabdi.extractor import extract_product_data
from suppliers.fetchers.pakhshabdi.extractor import extract_product_data
from products.services.productdata_to_json import product_to_json


AVAILABLE_PRODUCTS_FILE = "available_products.json"
PRODUCTDATA_FILE = "productdata.json"


def sync_products():

    available_products = load_json(AVAILABLE_PRODUCTS_FILE)
    productdata = load_json(PRODUCTDATA_FILE)

    # ایندکس محصولات بر اساس URL
    product_index = {
        item["supplier_url"]: item
        for item in productdata
    }

            
    for available in available_products:

        supplier_url = available["supplier_url"]

        # محصول وجود دارد
        if supplier_url in product_index:
            product = product_index[supplier_url]
            print(product)
            print(available["price"])
            if product["price"] != available["price"]:
                product["price"] = available["price"]
                save_json(PRODUCTDATA_FILE, productdata)
             
            if product["stock"] != available.get("quantity", 0):
                product["stock"] = available.get("quantity", 0)
                save_json(PRODUCTDATA_FILE, productdata)
    
        # محصول جدید
        else:

            product = extract_product_data(supplier_url)

            if product is None:
                continue

            productdata.append(
                product_to_json(product)
            )
            save_json(PRODUCTDATA_FILE, productdata)

    
    
if __name__ == "__main__":
    sync_products()
