from django.test import TestCase

from products.models import Product, ProductVariant
from suppliers.models import Supplier, SupplierOffer
from products.services.product_data import ProductData
from suppliers.sync.updater import update_offer


class UpdateOfferTest(TestCase):

    def setUp(self):
        self.supplier = Supplier.objects.create(
            name="Abdi",
            slug="abdi",
        )

        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            base_price=1000,

        )

        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="TEST-1",
        )

        self.offer = SupplierOffer.objects.create(
            supplier=self.supplier,
            variant=self.variant,
            purchase_price=1000,
            supplier_stock=10,
        )

    def test_update_stock(self):
        item = ProductData()
        item.name = "Test Product"
        item.price = 1000
        item.quantity = 5

        changed = update_offer(self.offer, item)

        self.offer.refresh_from_db()

        self.assertTrue(changed)
        self.assertEqual(self.offer.supplier_stock, 5)
        self.assertEqual(self.offer.purchase_price, 1000)
