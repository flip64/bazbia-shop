from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, Client
from django.urls import reverse
from products.models import Product, ProductVariant
from . import models as m


class VariantPickerTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            "manager", "test@example.com", "test"
        )
        self.client.force_login(self.user)
        self.product = Product.objects.create(
            name="سکه سوریه", slug="syria-coin", base_price=10000
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="SYR-1994", price=10000
        )
        self.issuer = m.CoinIssuer.objects.create(name="سوریه", slug="syria")
        self.coin = m.CoinType.objects.create(
            name="یک لیره", slug="lira", issuer=self.issuer
        )
        self.issue = m.CoinIssue.objects.create(coin_type=self.coin, year=1994)

    def url(self, name):
        return reverse("dashboard:coin_catalog:" + name) + "?kind=specimen"

    def test_search_by_product_and_sku(self):
        for q in ["سوریه", "SYR-1994"]:
            response = self.client.get(
                self.url("variant-lookup"), {"kind": "specimen", "q": q}
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["results"][0]["id"], self.variant.pk)
            self.assertIn("SYR-1994", response.json()["results"][0]["label"])

    def test_linked_variants_excluded_but_edit_keeps_current(self):
        specimen = m.CoinSpecimen.objects.create(issue=self.issue, variant=self.variant)
        self.assertEqual(
            self.client.get(self.url("variant-lookup")).json()["results"], []
        )
        url = reverse(
            "dashboard:coin_catalog:edit",
            kwargs={"kind": "specimen", "pk": specimen.pk},
        )
        self.assertContains(self.client.get(url), "SYR-1994")

    def test_empty_variant_form_still_has_search_and_create(self):
        ProductVariant.objects.all().delete()
        url = reverse("dashboard:coin_catalog:create", kwargs={"kind": "specimen"})
        response = self.client.get(url)
        self.assertContains(response, "جستجوی واریانت با نام محصول یا SKU")
        self.assertContains(response, "افزودن واریانت جدید")

    def test_create_is_zero_stock_and_selectable(self):
        response = self.client.post(
            self.url("variant-create"),
            {
                "product": self.product.pk,
                "sku": "NEW-SYR",
                "price": 12000,
                "stock": 999,
            },
        )
        self.assertEqual(response.status_code, 201, response.content)
        variant = ProductVariant.objects.get(pk=response.json()["id"])
        self.assertEqual(variant.stock, 0)
        self.assertIn("NEW-SYR", response.json()["label"])
        m.CoinSpecimen.objects.create(issue=self.issue, variant=variant)

    def test_invalid_price_discount_and_duplicate_rejected(self):
        for changes in [{"price": -1}, {"discount_price": 10000}, {"sku": "SYR-1994"}]:
            data = {"product": self.product.pk, "sku": "NEW", "price": 10000, **changes}
            response = self.client.post(self.url("variant-create"), data)
            self.assertEqual(response.status_code, 400)
        self.assertEqual(ProductVariant.objects.count(), 1)

    def test_permissions_for_search_and_create(self):
        staff = get_user_model().objects.create_user("staff", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.url("variant-lookup")).status_code, 403)
        staff.user_permissions.add(
            Permission.objects.get(codename="add_coinspecimen"),
            Permission.objects.get(codename="view_productvariant"),
        )
        self.assertEqual(self.client.get(self.url("variant-lookup")).status_code, 200)
        self.assertEqual(
            self.client.post(self.url("variant-create"), {}).status_code, 403
        )

    def test_pagination_is_bounded_and_validated(self):
        ProductVariant.objects.bulk_create(
            [
                ProductVariant(product=self.product, sku=f"P-{i:02}", price=1000)
                for i in range(25)
            ]
        )
        data = self.client.get(self.url("variant-lookup")).json()
        self.assertEqual(len(data["results"]), 20)
        self.assertTrue(data["has_more"])
        self.assertEqual(
            self.client.get(self.url("variant-lookup") + "&page=bad").status_code, 400
        )

    def test_product_lookup(self):
        response = self.client.get(
            self.url("variant-lookup") + "&target=product&q=سوریه"
        )
        self.assertEqual(response.json()["results"][0]["id"], self.product.pk)

    def test_csrf_and_get_cannot_create(self):
        self.assertEqual(self.client.get(self.url("variant-create")).status_code, 405)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(
            client.post(
                self.url("variant-create"),
                {"product": self.product.pk, "sku": "NEW", "price": 1000},
            ).status_code,
            403,
        )
