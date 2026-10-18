"""Regression coverage for the existing, non-coin storefront."""

from django.core.exceptions import ValidationError
from django.db.models import F
from django.test import TestCase
from products.models import Product, ProductVariant
from suppliers.models import Supplier, SupplierOffer
from inventory.models import InventoryLot
from orders.models import Order, OrderItem
from payments.models import Payment
from payments.services.payment_verify_service import PaymentVerifyService
from coins import test_operations as operations_tests
from coins import models as m


class OrdinaryProductsRegressionTests(TestCase):
    def setUp(self):
        operations_tests.CoinOperationsTests.setUp(self)
        self.normal_product = Product.objects.create(
            name="ظرف آشپزخانه", slug="normal", base_price=15000
        )
        self.normal = ProductVariant.objects.create(
            product=self.normal_product, sku="NORMAL", price=15000, stock=10
        )
        self.normal_lot = InventoryLot.objects.create(
            product_variant=self.normal,
            quantity_received=10,
            quantity_remaining=10,
            unit_cost=7000,
        )
        self.supplier = Supplier.objects.create(
            name="تأمین‌کننده عادی", slug="ordinary-supplier"
        )

    checkout = operations_tests.CoinOperationsTests.checkout

    def offer(self, variant=None, stock=20):
        return SupplierOffer.objects.create(
            supplier=self.supplier,
            variant=variant or self.normal,
            purchase_price=6000,
            supplier_stock=stock,
            supplier_url="https://example.com/normal",
        )

    def test_normal_stock_has_no_single_unit_limit(self):
        self.normal.stock = 500
        self.normal.save()
        self.normal.full_clean()
        self.normal.refresh_from_db()
        self.assertEqual(self.normal.stock, 500)

    def test_normal_save_queryset_and_bulk_update(self):
        ProductVariant.objects.filter(pk=self.normal.pk).update(stock=F("stock") + 5)
        self.normal.refresh_from_db()
        self.assertEqual(self.normal.stock, 15)
        self.normal.stock = 250
        ProductVariant.objects.bulk_update([self.normal], ["stock"])
        self.normal.refresh_from_db()
        self.assertEqual(self.normal.stock, 250)

    def test_normal_supplier_offer_and_group_updates(self):
        offer = self.offer(stock=500)
        offer.full_clean()
        SupplierOffer.objects.filter(pk=offer.pk).update(
            supplier_stock=F("supplier_stock") + 20
        )
        offer.refresh_from_db()
        self.assertEqual(offer.supplier_stock, 520)
        offer.supplier_stock = 800
        SupplierOffer.objects.bulk_update([offer], ["supplier_stock"])
        offer.refresh_from_db()
        self.assertEqual(offer.supplier_stock, 800)

    def test_bulk_offer_variant_reassignment_still_works(self):
        offer = self.offer()
        target = ProductVariant.objects.create(
            product=self.normal_product, sku="NORMAL-SECOND", price=12000, stock=20
        )
        offer.variant = target
        SupplierOffer.objects.bulk_update([offer], ["variant"])
        offer.refresh_from_db()
        self.assertEqual(offer.variant_id, target.pk)

    def test_expression_offer_reassignment_cannot_bypass_coin_guard(self):
        offer = self.offer()
        offer.variant = self.pack_variant
        with self.assertRaises(ValidationError):
            SupplierOffer.objects.bulk_update([offer], ["variant"])
        offer.refresh_from_db()
        self.assertEqual(offer.variant_id, self.normal.pk)

    def test_normal_bulk_create_not_restricted(self):
        second = ProductVariant(
            product=self.normal_product, sku="NORMAL-BULK", price=20000, stock=30
        )
        ProductVariant.objects.bulk_create([second])
        SupplierOffer.objects.bulk_create(
            [
                SupplierOffer(
                    supplier=self.supplier,
                    variant=second,
                    supplier_stock=90,
                    purchase_price=1000,
                )
            ]
        )
        self.assertEqual(second.supplier_offers.get().supplier_stock, 90)

    def test_normal_no_coin_images_or_publication_required(self):
        response = self.client.post(
            "/api/orders/cart/add/",
            {"variant_id": self.normal.pk, "quantity": 3},
            format="json",
        )
        self.assertEqual(response.status_code, 201, str(response.data))
        self.assertFalse(self.normal.images.exists())

    def test_normal_internal_checkout_cancel_and_empty_coin_snapshot(self):
        order = self.checkout(self.normal, 3)
        self.normal.refresh_from_db()
        self.normal_lot.refresh_from_db()
        self.assertEqual(
            (self.normal.stock, self.normal_lot.quantity_remaining), (7, 7)
        )
        self.assertEqual(order.items.get().catalog_snapshot, {})
        response = self.client.post(f"/api/orders/{order.pk}/cancel/")
        self.assertEqual(response.status_code, 200, str(response.data))
        self.normal.refresh_from_db()
        self.normal_lot.refresh_from_db()
        self.assertEqual(
            (self.normal.stock, self.normal_lot.quantity_remaining), (10, 10)
        )

    def test_normal_supplier_only_checkout_cancel(self):
        self.normal.stock = 0
        self.normal.save()
        self.normal_lot.quantity_remaining = 0
        self.normal_lot.save()
        offer = self.offer(stock=8)
        order = self.checkout(self.normal, 3)
        offer.refresh_from_db()
        self.assertEqual(offer.supplier_stock, 5)
        self.assertEqual(
            self.client.post(f"/api/orders/{order.pk}/cancel/").status_code, 200
        )
        offer.refresh_from_db()
        self.assertEqual(offer.supplier_stock, 8)

    def test_normal_mixed_internal_supplier_fulfilment(self):
        self.normal.stock = 1
        self.normal.save()
        self.normal_lot.quantity_remaining = 1
        self.normal_lot.save()
        offer = self.offer(stock=5)
        order = self.checkout(self.normal, 3)
        self.normal.refresh_from_db()
        offer.refresh_from_db()
        self.assertEqual((self.normal.stock, offer.supplier_stock), (0, 3))
        self.assertEqual(
            self.client.post(f"/api/orders/{order.pk}/cancel/").status_code, 200
        )
        self.normal.refresh_from_db()
        offer.refresh_from_db()
        self.assertEqual((self.normal.stock, offer.supplier_stock), (1, 5))

    def test_normal_discount_price_is_preserved(self):
        self.normal.discount_price = 12500
        self.normal.save(update_fields=["discount_price"])
        order = self.checkout(self.normal, 2)
        self.assertEqual(order.items.get().price, 12500)
        self.assertEqual(order.items_total, 25000)

    def test_normal_payment_success_and_paid_cancel_rules(self):
        order = self.checkout(self.normal, 2)
        payment = Payment.objects.create(
            order=order, amount=order.total_price, gateway="mock", authority="normal"
        )
        PaymentVerifyService(payment, "normal", "success").run()
        order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(order.status, "paid")
        self.assertFalse(payment.requires_review)
        self.assertEqual(
            self.client.post(f"/api/orders/{order.pk}/cancel/").status_code, 400
        )

    def test_normal_processing_cancel_keeps_previous_policy(self):
        order = self.checkout(self.normal)
        Payment.objects.create(
            order=order, amount=order.total_price, status=Payment.Status.PROCESSING
        )
        response = self.client.post(f"/api/orders/{order.pk}/cancel/")
        self.assertEqual(response.status_code, 200, str(response.data))

    def test_normal_orderitem_bulk_creation_still_allowed(self):
        order = Order.objects.create(user=self.user)
        OrderItem.objects.bulk_create(
            [OrderItem(order=order, variant=self.normal, price=15000, quantity=4)]
        )
        self.assertEqual(order.items.get().catalog_snapshot, {})

    def test_mixed_cart_has_snapshot_only_for_coin_item(self):
        self.ready()
        response = self.client.post(
            "/api/orders/cart/add/",
            {"variant_id": self.normal.pk, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        order = self.checkout(self.variant)
        self.assertTrue(order.items.get(variant=self.variant).catalog_snapshot)
        self.assertEqual(order.items.get(variant=self.normal).catalog_snapshot, {})

    ready = operations_tests.CoinOperationsTests.ready

    def test_mixed_batch_rollback_does_not_partially_change_normal_stock(self):
        self.variant.stock = 1
        self.variant.save()
        self.specimen.sale_mode = "unique"
        self.specimen.save()
        with self.assertRaises(ValidationError):
            ProductVariant.objects.filter(
                pk__in=[self.normal.pk, self.variant.pk]
            ).update(stock=200)
        self.normal.refresh_from_db()
        self.assertEqual(self.normal.stock, 10)
