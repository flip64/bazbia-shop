from suppliers.fetchers.pakhshabdi.json_loader import load_json
from products.services.productdata_from_json import product_from_json

from suppliers.fetchers.pakhshabdi.json_loader import load_available_products
from suppliers.fetchers.pakhshabdi.extractor import extract_product_data

PRODUCTDATA_FILE = "productdata.json"


def list_product():
    raw_products = load_json(PRODUCTDATA_FILE)

    product_data_list = []

    for item in raw_products:
        product_data = product_from_json(item)

        if product_data:
            product_data_list.append(product_data)

    return product_data_list
