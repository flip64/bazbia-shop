from django.db import transaction

from products.services.product_data import ProductData
from suppliers.fetchers.pakhshabdi.get_supplier_abdi import get_supplier_abdi
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

from suppliers.fetchers.pakhshabdi.sync.extractor import extract_product_data


@transaction.atomic
def create_product_from_url(url):
    data = extract_product_data(url)
    data.is_active = False
    product = create_product(data)

    variant = create_variant(product, data)

    create_specifications(product, data)

    create_tags(product, data)

    create_images(product, data)
    supplier =get_supplier_abdi()
    offer = create_supplier_offer(
        supplier=supplier,
        variant=variant,
        supplier_url= url ,
        purchase_price = data.price,
        supplier_stock=  data.quantity,
        supplier_product_name = data.name

       
    )

    create_price_history(offer, data.price)

    return product
