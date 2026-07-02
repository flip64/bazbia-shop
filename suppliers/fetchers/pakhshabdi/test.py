from django.test import TestCase

from suppliers.models import Supplier
from products.models import Product
from products.services.create_product_from_url import create_product_from_url


class CreateProductFromUrlTest(TestCase):

    def test_create_product(self):
        supplier = Supplier.objects.create(
            name="پخش عبدی",
        )

        url = "https://pakhshabdi.com/product/..."  # آدرس واقعی یک محصول

        product = create_product_from_url(url, supplier)

        self.assertIsNotNone(product.id)
        self.assertTrue(Product.objects.filter(id=product.id).exists())
