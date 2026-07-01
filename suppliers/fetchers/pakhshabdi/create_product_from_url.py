from django.db import transaction

from products.services.product_data import ProductData

from products.services.product_creator import (
    create_product,
    create_variant,
    create_specifications,
    create_tags,
    create_images,
)

from suppliers.services.offer_creator import (
    create_supplier_offer,
    create_price_history,
)

from suppliers.fetchers.pakhshabdi.extractor import extract_product_data


@transaction.atomic
def create_product_from_url(url, supplier):
    data = extract_product_data(url)

    product = create_product(data)

    variant = create_variant(product, data)

    create_specifications(product, data.specifications)

    create_tags(product, data.tags)

    create_images(product, data.images)

    offer = create_supplier_offer(
        supplier=supplier,
        variant=variant,
        data=data,
    )

    create_price_history(offer)

    return product
