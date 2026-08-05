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



@transaction.atomic
def create_product_from_productData(data):
    product = create_product(data)

    variant = create_variant(product, data)

    create_specifications(product, data)

    create_tags(product, data)

    create_images(product, data)
    offer = create_supplier_offer(
        supplier=data.supplier,
        variant=variant,
        supplier_url= data.supplier_url ,
        purchase_price = data.price,
        supplier_stock=  data.quantity,
        supplier_product_name = data.name

       
    )

    create_price_history(offer, data.price)

    return product
