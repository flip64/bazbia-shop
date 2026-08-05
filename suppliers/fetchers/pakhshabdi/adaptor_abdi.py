from suppliers.fetchers.pakhshabdi.json_loader import load_available_products
from suppliers.fetchers.pakhshabdi.extractor import extract_product_data


def list_product():
    raw_products = load_available_products()
    product_data_list = []

    for item in raw_products:
        product_data = extract_product_data(item["url"])

        if product_data:
            product_data_list.append(product_data)

    return product_data_list