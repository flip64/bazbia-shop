from copy import deepcopy
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import F
from django.test import TestCase
from rest_framework.test import APIClient
from products.models import Product, ProductVariant
from suppliers.models import Supplier, SupplierOffer
from inventory.models import InventoryLot
from orders.models import Order, OrderItem, Cart
from customers.models import Customer, CustomerAddress
from payments.models import Payment
from payments.services.payment_verify_service import PaymentVerifyService
from coins import models as m
from coins.testing import publish_fixture
from coins.services import set_publication
from coins.assembly import assemble_pack


class CoinOperationsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="collector", password="test")
        self.staff = User.objects.create_user(
            username="manager", password="test", is_staff=True
        )
        customer = Customer.objects.create(user=self.user)
        self.address = CustomerAddress.objects.create(
            customer=customer, province="تهران", city="قدس", address="آدرس آزمایشی"
        )
        self.issuer = m.CoinIssuer.objects.create(name="ایران", slug="iran")
        self.coin = m.CoinType.objects.create(
            name="۲۵۰ ریالی",
            slug="250-rial",
            issuer=self.issuer,
            calendar="solar_hijri",
        )
        self.issue = m.CoinIssue.objects.create(
            coin_type=self.coin, year=1373, calendar="solar_hijri"
        )
        self.product = Product.objects.create(
            name="سکه", slug="single", base_price=10000
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="SINGLE", price=10000, stock=5
        )
        self.specimen = m.CoinSpecimen.objects.create(
            issue=self.issue,
            variant=self.variant,
            sale_mode="similar",
            condition_grade="xf",
        )
        self.lot = InventoryLot.objects.create(
            product_variant=self.variant,
            quantity_received=5,
            quantity_remaining=5,
            unit_cost=3000,
        )
        self.pack_product = Product.objects.create(
            name="پک", slug="pack", base_price=30000
        )
        self.pack_variant = ProductVariant.objects.create(
            product=self.pack_product, sku="PACK", price=30000, stock=0
        )
        self.pack = m.CoinPack.objects.create(
            product=self.pack_product,
            year=1373,
            calendar="solar_hijri",
            issuer=self.issuer,
        )
        self.pv = m.CoinPackVariant.objects.create(
            pack=self.pack, variant=self.pack_variant
        )
        self.item = m.CoinPackItem.objects.create(
            pack_variant=self.pv, issue=self.issue, quantity=2, condition_grade="xf"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def sources(self, qty=2):
        return [
            {"item_id": self.item.pk, "variant_id": self.variant.pk, "quantity": qty}
        ]

    def ready(self):
        publish_fixture(self.specimen)
        publish_fixture(self.pv)

    def checkout(self, variant=None, quantity=1):
        variant = variant or self.variant
        added = self.client.post(
            "/api/orders/cart/add/",
            {"variant_id": variant.pk, "quantity": quantity},
            format="json",
        )
        self.assertIn(added.status_code, (200, 201), str(added.data))
        response = self.client.post(
            "/api/orders/create/",
            {
                "address_id": self.address.pk,
                "shipping_quote_id": "test-quote",
                "shipping_method_code": "post_pishtaz",
                "payment_method": "online",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, str(response.data))
        return Order.objects.get(user=self.user)

    def test_disabled_variant_blocks_add_and_existing_cart_checkout(self):
        self.ready()
        added = self.client.post("/api/orders/cart/add/", {"variant_id": self.variant.pk, "quantity": 1}, format="json")
        self.assertIn(added.status_code, (200, 201))
        self.variant.is_sellable = False
        self.variant.save(update_fields=["is_sellable"])
        added_again = self.client.post("/api/orders/cart/add/", {"variant_id": self.variant.pk, "quantity": 1}, format="json")
        self.assertEqual(added_again.status_code, 400)
        checkout = self.client.post("/api/orders/create/", {
            "address_id": self.address.pk, "shipping_quote_id": "test-quote",
            "shipping_method_code": "post_pishtaz", "payment_method": "online",
        }, format="json")
        self.assertEqual(checkout.status_code, 400)
        self.assertFalse(Order.objects.exists())
        self.variant.refresh_from_db()
        self.lot.refresh_from_db()
        self.assertEqual(self.variant.stock, 5)
        self.assertEqual(self.lot.quantity_remaining, 5)

    def test_unique_save_and_queryset_update_rejected_atomically(self):
        self.variant.stock = 1
        self.variant.save()
        self.specimen.sale_mode = "unique"
        self.specimen.save()
        self.variant.stock = 2
        with self.assertRaises(ValidationError):
            self.variant.save(update_fields=["stock"])
        with self.assertRaises(ValidationError):
            ProductVariant.objects.filter(pk=self.variant.pk).update(
                stock=F("stock") + 1
            )
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 1)
        self.variant.stock = 3
        with self.assertRaises(ValidationError):
            ProductVariant.objects.bulk_update([self.variant], ["stock"])
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 1)

    def test_similar_stock_many_allowed(self):
        ProductVariant.objects.filter(pk=self.variant.pk).update(stock=20)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 20)

    def test_supplier_offer_for_pack_rejected_in_save_and_bulk(self):
        supplier = Supplier.objects.create(name="پخش", slug="supplier")
        for bulk in (False, True):
            with self.assertRaises(ValidationError):
                offer = SupplierOffer(
                    supplier=supplier,
                    variant=self.pack_variant,
                    purchase_price=1000,
                    supplier_stock=10,
                )
                SupplierOffer.objects.bulk_create([offer]) if bulk else offer.save()
        self.assertFalse(
            SupplierOffer.objects.filter(variant=self.pack_variant).exists()
        )

    def test_existing_offer_cannot_be_activated_for_unique(self):
        supplier = Supplier.objects.create(name="پخش", slug="supplier")
        offer = SupplierOffer.objects.create(
            supplier=supplier,
            variant=self.variant,
            purchase_price=1000,
            supplier_stock=10,
            is_available=False,
        )
        self.variant.stock = 1
        self.variant.save()
        self.specimen.sale_mode = "unique"
        self.specimen.save()
        with self.assertRaises(ValidationError):
            SupplierOffer.objects.filter(pk=offer.pk).update(is_available=True)
        offer.refresh_from_db()
        self.assertFalse(offer.is_available)

    def test_publish_rejects_missing_images_and_empty_pack(self):
        with self.assertRaises(ValidationError):
            set_publication(self.specimen, True)
        self.item.delete()
        with self.assertRaises(ValidationError):
            set_publication(self.pv, True)

    def test_draft_cannot_enter_cart_or_order_directly(self):
        response = self.client.post(
            "/api/orders/cart/add/",
            {"variant_id": self.variant.pk, "quantity": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        order = Order.objects.create(user=self.user)
        with self.assertRaises(ValidationError):
            OrderItem.objects.create(order=order, variant=self.variant, price=10000)
        self.assertFalse(order.items.exists())

    def test_pack_assembly_moves_stock_and_cost_exactly_once(self):
        event = assemble_pack(
            pack_variant_id=self.pv.pk,
            quantity=2,
            sources=self.sources(4),
            request_key="pack-1",
        )
        self.assertEqual(event.total_cost, Decimal("12000"))
        self.variant.refresh_from_db()
        self.pack_variant.refresh_from_db()
        self.lot.refresh_from_db()
        self.assertEqual(
            (self.variant.stock, self.pack_variant.stock, self.lot.quantity_remaining),
            (1, 2, 1),
        )
        self.assertEqual(
            sum(l.quantity_remaining * l.unit_cost for l in event.output_lots.all()),
            Decimal("12000"),
        )
        again = assemble_pack(
            pack_variant_id=self.pv.pk,
            quantity=2,
            sources=self.sources(4),
            request_key="pack-1",
        )
        self.assertEqual(event.pk, again.pk)
        self.pack_variant.refresh_from_db()
        self.assertEqual(self.pack_variant.stock, 2)
        with self.assertRaises(ValidationError):
            assemble_pack(
                pack_variant_id=self.pv.pk,
                quantity=1,
                sources=self.sources(2),
                request_key="pack-1",
            )

    def test_failed_assembly_rolls_back_everything(self):
        with self.assertRaises(ValidationError):
            assemble_pack(
                pack_variant_id=self.pv.pk,
                quantity=3,
                sources=self.sources(6),
                request_key="insufficient",
            )
        self.variant.refresh_from_db()
        self.lot.refresh_from_db()
        self.assertEqual((self.variant.stock, self.lot.quantity_remaining), (5, 5))
        self.assertFalse(m.PackAssembly.objects.exists())

    def test_unique_destination_failure_rolls_back_consumption(self):
        self.pv.sale_mode = "unique"
        self.pv.save()
        with self.assertRaises(ValidationError):
            assemble_pack(
                pack_variant_id=self.pv.pk,
                quantity=2,
                sources=self.sources(4),
                request_key="unique-pack",
            )
        self.variant.refresh_from_db()
        self.lot.refresh_from_db()
        self.assertEqual((self.variant.stock, self.lot.quantity_remaining), (5, 5))
        self.assertFalse(m.PackAssembly.objects.exists())

    def test_assembled_contents_cannot_be_redefined(self):
        assemble_pack(
            pack_variant_id=self.pv.pk,
            quantity=1,
            sources=self.sources(),
            request_key="freeze",
        )
        self.item.quantity = 3
        with self.assertRaises(ValidationError):
            self.item.save()

    def test_snapshot_frozen_after_catalog_changes(self):
        self.ready()
        order = self.checkout()
        item = order.items.get()
        original = deepcopy(item.catalog_snapshot)
        self.coin.name = "عنوان جدید"
        self.coin.save()
        self.specimen.condition_notes = "توضیح جدید"
        self.specimen.save()
        item.refresh_from_db()
        self.assertEqual(item.catalog_snapshot, original)
        self.assertNotIn("storage_location", str(original))
        item.catalog_snapshot = {}
        with self.assertRaises(ValidationError):
            item.save()

    def test_checkout_and_cancel_restore_stock_and_lot_once(self):
        self.ready()
        order = self.checkout(quantity=2)
        self.variant.refresh_from_db()
        self.lot.refresh_from_db()
        self.assertEqual((self.variant.stock, self.lot.quantity_remaining), (3, 3))
        response = self.client.post(f"/api/orders/{order.pk}/cancel/")
        self.assertEqual(response.status_code, 200, str(response.data))
        response = self.client.post(f"/api/orders/{order.pk}/cancel/")
        self.assertEqual(response.status_code, 400)
        self.variant.refresh_from_db()
        self.lot.refresh_from_db()
        self.assertEqual((self.variant.stock, self.lot.quantity_remaining), (5, 5))

    def test_pack_checkout_does_not_consume_loose_stock_twice(self):
        self.ready()
        assemble_pack(
            pack_variant_id=self.pv.pk,
            quantity=1,
            sources=self.sources(),
            request_key="checkout-pack",
        )
        order = self.checkout(self.pack_variant)
        self.variant.refresh_from_db()
        self.pack_variant.refresh_from_db()
        self.assertEqual((self.variant.stock, self.pack_variant.stock), (3, 0))
        self.assertEqual(order.items.get().catalog_snapshot["variant"]["coin_count"], 2)
        response = self.client.post(f"/api/orders/{order.pk}/cancel/")
        self.assertEqual(response.status_code, 200)
        self.variant.refresh_from_db()
        self.pack_variant.refresh_from_db()
        self.assertEqual((self.variant.stock, self.pack_variant.stock), (3, 1))

    def test_mock_success_and_paid_order_cannot_be_cancelled(self):
        self.ready()
        order = self.checkout()
        payment = Payment.objects.create(
            order=order,
            amount=order.total_price,
            gateway="mock",
            authority="mock-authority",
        )
        PaymentVerifyService(payment, "mock-authority", "success").run()
        order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(order.status, "paid")
        self.assertFalse(payment.requires_review)
        self.assertEqual(
            self.client.post(f"/api/orders/{order.pk}/cancel/").status_code, 400
        )

    def test_processing_payment_blocks_cancellation(self):
        self.ready()
        order = self.checkout()
        Payment.objects.create(
            order=order, amount=order.total_price, status=Payment.Status.PROCESSING
        )
        self.assertEqual(
            self.client.post(f"/api/orders/{order.pk}/cancel/").status_code, 400
        )
        order.refresh_from_db()
        self.assertEqual(order.status, "pending")

    def test_late_success_preserves_cancelled_order_and_records_review(self):
        self.ready()
        order = self.checkout()
        payment = Payment.objects.create(
            order=order, amount=order.total_price, gateway="mock", authority="late"
        )
        self.assertEqual(
            self.client.post(f"/api/orders/{order.pk}/cancel/").status_code, 200
        )
        PaymentVerifyService(payment, "late", "success").run()
        order.refresh_from_db()
        payment.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(payment.status, Payment.Status.SUCCESSFUL)
        self.assertTrue(payment.requires_review)
        self.assertEqual(self.variant.stock, 5)

    def test_staff_only_operational_endpoints(self):
        data = {
            "pack_variant_id": self.pv.pk,
            "quantity": 1,
            "sources": self.sources(),
            "request_key": "staff",
        }
        self.assertEqual(
            self.client.post(
                "/api/coins/manage/assemble/", data, format="json"
            ).status_code,
            403,
        )
        self.client.force_authenticate(self.staff)
        response = self.client.post("/api/coins/manage/assemble/", data, format="json")
        self.assertEqual(response.status_code, 200, str(response.data))

    def test_deleting_required_image_hides_listing_and_blocks_purchase(self):
        self.ready()
        self.specimen.variant.images.filter(coin_detail__view_type="reverse").delete()
        response = self.client.get("/api/coins/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        response = self.client.post(
            "/api/orders/cart/add/",
            {"variant_id": self.variant.pk, "quantity": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_publication_endpoint_reports_missing_images_then_allows_publish(self):
        self.client.force_authenticate(self.staff)
        url = f"/api/coins/manage/coin/{self.specimen.pk}/publish/"
        response = self.client.post(url, {"is_published": True}, format="json")
        self.assertEqual(response.status_code, 400)
        publish_fixture(self.specimen)
        response = self.client.post(url, {"is_published": False}, format="json")
        self.assertEqual(response.status_code, 200)
        self.specimen.refresh_from_db()
        self.assertFalse(self.specimen.is_published)

    def test_bulk_snapshot_rewrite_rejected(self):
        self.ready()
        order = self.checkout()
        with self.assertRaises(ValidationError):
            order.items.update(catalog_snapshot={})
        self.assertTrue(order.items.get().catalog_snapshot)

    def test_bulk_coin_order_creation_rejected(self):
        self.ready()
        order = Order.objects.create(user=self.user)
        with self.assertRaises(ValidationError):
            OrderItem.objects.bulk_create(
                [OrderItem(order=order, variant=self.variant, price=10000)]
            )

    def test_stock_lot_mismatch_rejected_before_order(self):
        self.ready()
        self.variant.stock = 10
        self.variant.save()
        response = self.client.post(
            "/api/orders/cart/add/",
            {"variant_id": self.variant.pk, "quantity": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.filter(user=self.user).exists())

    def test_unrelated_products_keep_normal_inventory_behavior(self):
        product = Product.objects.create(
            name="کالای عادی", slug="normal", base_price=100
        )
        variant = ProductVariant.objects.create(
            product=product, sku="NORMAL", price=100, stock=100
        )
        ProductVariant.objects.filter(pk=variant.pk).update(stock=F("stock") + 2)
        variant.refresh_from_db()
        self.assertEqual(variant.stock, 102)

    def test_pending_order_rejects_second_buyer_for_unique(self):
        self.variant.stock = 1
        self.variant.save()
        self.lot.quantity_remaining = 1
        self.lot.save()
        self.specimen.sale_mode = "unique"
        self.specimen.save()
        self.ready()
        self.checkout()
        other = User.objects.create_user(username="other")
        self.client.force_authenticate(other)
        response = self.client.post(
            "/api/orders/cart/add/",
            {"variant_id": self.variant.pk, "quantity": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_audit_command_read_only(self):
        from django.core.management import call_command
        from io import StringIO

        output = StringIO()
        call_command("audit_coins", stdout=output)
        self.assertIn("no errors", output.getvalue())
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 5)

    def test_unique_reservation_prevents_manual_restock_until_cancelled(self):
        self.variant.stock = 1
        self.variant.save()
        self.lot.quantity_remaining = 1
        self.lot.save()
        self.specimen.sale_mode = "unique"
        self.specimen.save()
        self.ready()
        order = self.checkout()
        with self.assertRaises(ValidationError):
            ProductVariant.objects.filter(pk=self.variant.pk).update(stock=1)
        response = self.client.post(f"/api/orders/{order.pk}/cancel/")
        self.assertEqual(response.status_code, 200, str(response.data))
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 1)

    def test_assembly_rounding_preserves_total_purchase_cost(self):
        InventoryLot.objects.create(
            product_variant=self.variant,
            quantity_received=1,
            quantity_remaining=1,
            unit_cost=3001,
        )
        self.variant.stock = 6
        self.variant.save()
        event = assemble_pack(
            pack_variant_id=self.pv.pk,
            quantity=3,
            sources=self.sources(6),
            request_key="rounding",
        )
        self.assertEqual(event.total_cost, Decimal("18001"))
        self.assertEqual(
            sum(l.quantity_remaining * l.unit_cost for l in event.output_lots.all()),
            Decimal("18001"),
        )
        self.assertEqual(sum(l.quantity_remaining for l in event.output_lots.all()), 3)

    def test_payment_creation_and_retry_verification_are_idempotent(self):
        from payments.services.payment_create_service import PaymentCreateService

        self.ready()
        order = self.checkout()
        result = PaymentCreateService(
            order, "https://example.com/payment/callback"
        ).run()
        self.assertEqual(result.payment.status, Payment.Status.PROCESSING)
        self.assertEqual(result.payment.amount, order.total_price)
        verify = PaymentVerifyService(
            result.payment, result.payment.authority, "success"
        )
        verify.run()
        verify.run()
        self.assertEqual(
            Payment.objects.filter(
                order=order, status=Payment.Status.SUCCESSFUL
            ).count(),
            1,
        )
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 4)

    def test_mock_verification_rejects_real_gateway_payment(self):
        self.ready()
        order = self.checkout()
        payment = Payment.objects.create(
            order=order, amount=order.total_price, gateway="zarinpal", authority="real"
        )
        with self.assertRaises(ValueError):
            PaymentVerifyService(payment, "real", "success").run()
        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(order.status, "pending")
