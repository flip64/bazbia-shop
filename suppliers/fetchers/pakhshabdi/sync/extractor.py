from products.services.product_data import ProductData

from .abdi_fetcher import (
    fetch_product_details,
    extract_quantity,
    extract_product_images,
    extract_specifications,
    extract_tags,
)


def extract_product_data(url):
    data = ProductData()

    name, price = fetch_product_details(url)

    data.name = name
    data.price = price or 0
    data.quantity = extract_quantity(url) or 0

    data.images = extract_product_images(url)
    data.specifications = extract_specifications(url)
    data.tags = extract_tags(url)

    data.supplier_url = url

    return data
