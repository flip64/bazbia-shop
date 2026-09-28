from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from products.models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductVariant,
)

from basalam_integration.models import (
    BasalamCategory,
    BasalamCategoryMapping,
    BasalamProductMapping,
    BasalamVariationMapping,
)
from basalam_integration.services.product_service import (
    build_product_sync_plan,
    set_product_active_on_basalam,
    sync_product_to_basalam,
)
from basalam_integration.services.client import BasalamAPIError


@override_settings(BASALAM_SYNC_ENABLED=True)
class ProductSyncServiceTests(TestCase):
    def setUp(self):
        category = Category.objects.create(
            name="پوشاک",
            slug="clothes",
        )
        basalam_category = BasalamCategory.objects.create(
            basalam_category_id=123,
            title="پوشاک",
        )
        BasalamCategoryMapping.objects.create(
            bazbia_category=category,
            basalam_category=basalam_category,
        )
        self.product = Product.objects.create(
            name="محصول آزمایشی",
            slug="test-product",
            base_price=100000,
            category=category,
        )
        self.product_mapping = BasalamProductMapping.objects.create(
            product=self.product,
            basalam_product_id=9001,
        )
        self.attribute = Attribute.objects.create(name="رنگ")

    def create_variant(self, *, sku, value):
        attribute_value = AttributeValue.objects.create(
            attribute=self.attribute,
            value=value,
        )
        variant = ProductVariant.objects.create(
            product=self.product,
            sku=sku,
            price=100000,
            stock=10,
        )
        variant.attributes.add(attribute_value)
        return variant

    def test_plan_detects_new_and_existing_variants(self):
        existing = self.create_variant(sku="SKU-OLD", value="قرمز")
        new = self.create_variant(sku="SKU-NEW", value="آبی")
        BasalamVariationMapping.objects.create(
            variant=existing,
            product_mapping=self.product_mapping,
            basalam_variation_id=7001,
        )

        plan = build_product_sync_plan(self.product)

        self.assertEqual(plan.existing_variant_ids, (existing.pk,))
        self.assertEqual(plan.new_variant_ids, (new.pk,))

    @patch(
        "basalam_integration.services.product_service."
        "calculate_variant_basalam_stock",
        return_value=4,
    )
    @patch(
        "basalam_integration.services.product_service."
        "calculate_variant_basalam_price",
        return_value=118000,
    )
    def test_sync_adds_new_variant_and_saves_mapping(
        self,
        _price_mock,
        _stock_mock,
    ):
        existing = self.create_variant(sku="SKU-OLD", value="قرمز")
        new = self.create_variant(sku="SKU-NEW", value="آبی")
        BasalamVariationMapping.objects.create(
            variant=existing,
            product_mapping=self.product_mapping,
            basalam_variation_id=7001,
        )
        client = Mock()
        client.update_product.return_value = {
            "id": 9001,
            "variants": [
                {"id": 7001, "sku": "SKU-OLD"},
                {"id": 7002, "sku": "SKU-NEW"},
            ],
        }

        result = sync_product_to_basalam(
            self.product,
            client=client,
        )

        self.assertEqual(result.added_count, 1)
        self.assertEqual(result.updated_count, 1)
        self.assertTrue(
            BasalamVariationMapping.objects.filter(
                variant=new,
                basalam_variation_id=7002,
            ).exists()
        )
        payload = client.update_product.call_args.kwargs["payload"]
        self.assertEqual(len(payload["variants"]), 2)
        client.update_product_variation.assert_not_called()

    @patch(
        "basalam_integration.services.product_service."
        "calculate_variant_basalam_stock",
        return_value=3,
    )
    @patch(
        "basalam_integration.services.product_service."
        "calculate_variant_basalam_price",
        return_value=120000,
    )
    def test_sync_updates_mapped_variant_without_product_patch(
        self,
        _price_mock,
        _stock_mock,
    ):
        variant = self.create_variant(sku="SKU-OLD", value="قرمز")
        BasalamVariationMapping.objects.create(
            variant=variant,
            product_mapping=self.product_mapping,
            basalam_variation_id=7001,
        )
        client = Mock()
        client.update_product_variation.return_value = {}

        result = sync_product_to_basalam(
            self.product,
            client=client,
        )

        self.assertEqual(result.added_count, 0)
        self.assertEqual(result.updated_count, 1)
        client.update_product.assert_not_called()
        client.update_product_variation.assert_called_once_with(
            product_id=9001,
            variation_id=7001,
            payload={
                "primary_price": 120000,
                "stock": 3,
                "sku": "SKU-OLD",
            },
        )

    def test_bulk_command_previews_all_connected_products(self):
        self.create_variant(sku="SKU-NEW", value="آبی")
        stdout = StringIO()

        call_command("sync_basalam_products", stdout=stdout)

        output = stdout.getvalue()
        self.assertIn("تعداد محصولات قابل بررسی: 1", output)
        self.assertIn("واریانت جدید: 1", output)
        self.assertIn("پیش‌نمایش تمام شد", output)

    @patch(
        "basalam_integration.management.commands."
        "sync_basalam_products.sync_product_to_basalam"
    )
    def test_bulk_command_commits_with_shared_sync_service(
        self,
        sync_mock,
    ):
        self.create_variant(sku="SKU-NEW", value="آبی")
        sync_mock.return_value = SimpleNamespace(
            added_count=1,
            updated_count=0,
        )
        stdout = StringIO()

        call_command(
            "sync_basalam_products",
            "--commit",
            stdout=stdout,
        )

        sync_mock.assert_called_once()
        self.assertIn("موفق: 1", stdout.getvalue())

    def test_deactivate_product_uses_unpublished_status(self):
        self.create_variant(sku="SKU-ONE", value="قرمز")
        client = Mock()
        client.update_product.return_value = {}

        result = set_product_active_on_basalam(
            self.product,
            active=False,
            client=client,
        )

        self.assertFalse(result.stock_zero_fallback)
        client.update_product.assert_called_once_with(
            product_id=9001,
            payload={"status": 3790},
        )

    def test_deactivate_falls_back_to_zero_stock(self):
        self.create_variant(sku="SKU-ONE", value="قرمز")
        client = Mock()
        client.update_product.side_effect = [
            BasalamAPIError("status rejected"),
            {},
        ]

        result = set_product_active_on_basalam(
            self.product,
            active=False,
            client=client,
        )

        self.assertTrue(result.stock_zero_fallback)
        self.assertEqual(client.update_product.call_count, 2)
        self.assertEqual(
            client.update_product.call_args_list[1].kwargs,
            {"product_id": 9001, "payload": {"stock": 0}},
        )

    def test_dashboard_basalam_page_is_available_to_staff(self):
        user = get_user_model().objects.create_user(
            username="staff",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:basalam_products"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "مدیریت محصولات باسلام")
        self.assertContains(response, self.product.name)

    @patch(
        "dashboard.views.basalam_views.sync_product_to_basalam"
    )
    def test_dashboard_sync_action_calls_shared_service(self, sync_mock):
        user = get_user_model().objects.create_user(
            username="operator",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(user)
        sync_mock.return_value = SimpleNamespace(
            added_count=1,
            updated_count=2,
        )

        response = self.client.post(
            reverse("dashboard:basalam_products"),
            {"product_id": self.product.pk, "action": "sync"},
        )

        self.assertEqual(response.status_code, 302)
        sync_mock.assert_called_once()
