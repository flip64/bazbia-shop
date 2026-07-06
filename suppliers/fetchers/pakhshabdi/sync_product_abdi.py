# -*- coding: utf-8 -*-

from suppliers.fetchers.pakhshabdi.json_loader import load_json
from suppliers.fetchers.pakhshabdi.save_json import save_json

from suppliers.fetchers.pakhshabdi.extractor import extract_product_data
from products.services.product_to_json import product_to_json


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

        url = available["supplier_url"]

        # محصول وجود دارد
        if url in product_index:

            product = product_index[url]

            product["price"] = available["price"]
            product["quantity"] = available.get("quantity", 0)

        # محصول جدید
        else:

            product = extract(url)

            if product is None:
                continue

            productdata.append(
                product_to_json(product)
            )

    save_json(PRODUCTDATA_FILE, productdata)


if __name__ == "__main__":
    sync_products()
