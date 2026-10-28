from coins.testing import publish_fixture
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from coins import models as m
from products.models import Product, ProductVariant, ProductVariantImage
from suppliers.models import Supplier, SupplierOffer


class CoinAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.issuer = m.CoinIssuer.objects.create(name="ایران", slug="iran")
        cls.coin = m.CoinType.objects.create(
            name="۲۵۰ ریالی",
            slug="250-rial",
            is_published=True,
            issuer=cls.issuer,
            calendar=m.Calendar.SOLAR_HIJRI,
        )
        cls.issue = m.CoinIssue.objects.create(
            coin_type=cls.coin, year=1373, calendar=m.Calendar.SOLAR_HIJRI
        )
        cls.old_issue = m.CoinIssue.objects.create(
            coin_type=cls.coin, year=1374, calendar=m.Calendar.SOLAR_HIJRI
        )
        cls.product = Product.objects.create(
            name="سکه تکی", slug="single", base_price=10000
        )
        cls.variant = ProductVariant.objects.create(
            product=cls.product, sku="COIN-1", price=10000, discount_price=9000, stock=1
        )
        cls.specimen = m.CoinSpecimen.objects.create(
            issue=cls.issue,
            variant=cls.variant,
            condition_grade="xf",
            storage_location="SECRET-LOCATION",
        )
        cls.empty_variant = ProductVariant.objects.create(
            product=cls.product, sku="COIN-2", price=3000, stock=0
        )
        cls.empty_specimen = m.CoinSpecimen.objects.create(
            issue=cls.old_issue, variant=cls.empty_variant, condition_grade="vf"
        )
        cls.image = ProductVariantImage.objects.create(
            variant=cls.variant, source_url="https://example.com/coin.jpg", is_main=True
        )
        m.CoinImageDetail.objects.create(image=cls.image, view_type="obverse")
        cls.pack_product = Product.objects.create(
            name="پک ۱۳۷۳", slug="pack-1373", base_price=20000
        )
        cls.pack = m.CoinPack.objects.create(
            product=cls.pack_product,
            year=1373,
            calendar=m.Calendar.SOLAR_HIJRI,
            issuer=cls.issuer,
        )
        cls.pack_variant = ProductVariant.objects.create(
            product=cls.pack_product, sku="PACK-1", price=20000, stock=2
        )
        cls.pv = m.CoinPackVariant.objects.create(
            pack=cls.pack, variant=cls.pack_variant, storage_location="PACK-SECRET"
        )
        cls.item = m.CoinPackItem.objects.create(
            pack_variant=cls.pv, issue=cls.issue, quantity=3, condition_grade="xf"
        )

        publish_fixture(cls.specimen)
        publish_fixture(cls.empty_specimen)
        publish_fixture(cls.pv)

    def setUp(self):
        self.client = APIClient()

    def get(self, path="", **params):
        response = self.client.get("/api/coins/" + path, params)
        self.assertEqual(response.status_code, 200, str(response.data))
        return response.data

    def test_list_summary_and_pagination(self):
        data = self.get()
        self.assertEqual(data["count"], 1)
        card = data["results"][0]
        self.assertEqual(card["min_price"], "9000")
        self.assertTrue(card["in_stock"])
        self.assertEqual(card["currency"], "IRT")

    def test_available_price_filter_uses_matching_specimen(self):
        card = self.get(in_stock="true")["results"][0]
        self.assertEqual(card["min_price"], "9000")
        self.assertEqual(card["image"]["url"], "https://example.com/coin.jpg")

    def test_filter_year_matches_actual_issue_not_type_range(self):
        self.assertEqual(self.get(year=1373, calendar="solar_hijri")["count"], 1)
        self.assertEqual(self.get(year=1375, calendar="solar_hijri")["count"], 0)

    def test_same_specimen_must_match_all_filters(self):
        self.assertEqual(
            self.get(year=1373, calendar="solar_hijri", condition="vf")["count"], 0
        )
        self.assertEqual(
            self.get(year=1373, calendar="solar_hijri", max_price=5000)["count"], 0
        )

    def test_invalid_filters_are_400(self):
        for params in (
            {"year": "1373"},
            {"year": "x", "calendar": "solar_hijri"},
            {"in_stock": "maybe"},
            {"calendar": "unknown"},
            {"ordering": "stock"},
            {"min_price": -1},
            {"min_price": 100, "max_price": 10},
            {"page_size": 101},
            {"page": 0},
            {"secret": 1},
            {"is_complete": True},
            {"year": 1373, "year_min": 1372, "calendar": "solar_hijri"},
        ):
            with self.subTest(params=params):
                response = self.client.get("/api/coins/", params)
                self.assertEqual(response.status_code, 400, str(response.data))

    def test_detail_public_fields_and_cart_identity(self):
        data = self.get("250-rial/")
        sample = data["issues"][0]["specimens"][0]
        self.assertEqual(sample["variant_id"], self.variant.pk)
        self.assertEqual(sample["effective_price"], "9000")
        self.assertTrue(sample["can_purchase"])
        self.assertNotIn("storage_location", sample)
        self.assertNotIn("purchase_price", str(data))
        self.assertNotIn("SECRET-LOCATION", str(data))
        self.assertFalse(data["issues"][1]["specimens"][0]["can_purchase"])

    def test_pack_contents_and_count(self):
        card = self.get("packs/")["results"][0]
        self.assertEqual(card["slug"], "pack-1373")
        self.assertEqual(card["min_price"], "20000")
        data = self.get("packs/pack-1373/")
        variant = data["variants"][0]
        self.assertEqual(variant["coin_count"], 3)
        self.assertEqual(variant["items"][0]["issue_id"], self.issue.pk)
        self.assertEqual(variant["variant_id"], self.pack_variant.pk)
        self.assertNotIn("PACK-SECRET", str(data))

    def test_pack_filters(self):
        self.assertEqual(
            self.get("packs/", year=1373, calendar="solar_hijri", condition="xf")[
                "count"
            ],
            1,
        )
        self.assertEqual(self.get("packs/", condition="vf")["count"], 0)
        self.assertEqual(self.get("packs/", is_complete="true")["count"], 0)

    def test_inactive_products_hide_sales_but_keep_published_catalog(self):
        self.product.is_active = False
        self.product.save()
        self.pack_product.is_active = False
        self.pack_product.save()
        self.assertEqual(self.get()["count"], 1)
        self.assertEqual(self.get("packs/")["count"], 0)
        response = self.client.get("/api/coins/250-rial/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(not issue["specimens"] for issue in response.data["issues"]))
        self.assertEqual(
            self.client.get("/api/coins/packs/pack-1373/").status_code, 404
        )
        self.assertEqual(len(self.get("filters/")["issuers"]), 1)

    def test_inactive_sample_hidden_in_active_type(self):
        self.product.is_active = False
        self.product.save()
        other_product = Product.objects.create(
            name="دیگر", slug="other", base_price=12000
        )
        variant = ProductVariant.objects.create(
            product=other_product, sku="OTHER", price=12000, stock=1
        )
        publish_fixture(
            m.CoinSpecimen.objects.create(issue=self.issue, variant=variant)
        )
        data = self.get("250-rial/")
        self.assertEqual(len(data["issues"][0]["specimens"]), 1)
        self.assertEqual(data["issues"][0]["specimens"][0]["variant_id"], variant.pk)
        self.assertEqual(len(data["issues"]), 2)
        self.assertEqual(data["issues"][1]["specimens"], [])

    def test_supplier_stock_agrees_with_existing_service(self):
        self.empty_specimen.sale_mode = "similar"
        self.empty_specimen.save()
        supplier = Supplier.objects.create(name="تأمین‌کننده", slug="test")
        SupplierOffer.objects.create(
            supplier=supplier,
            variant=self.empty_variant,
            purchase_price=1000,
            supplier_stock=4,
        )
        data = self.get("250-rial/")
        self.assertEqual(data["issues"][1]["specimens"][0]["available_stock"], 4)
        self.assertTrue(data["issues"][1]["specimens"][0]["can_purchase"])
        supplier.is_active = False
        supplier.save()
        data = self.get("250-rial/")
        self.assertEqual(data["issues"][1]["specimens"][0]["available_stock"], 0)

    def test_filter_options(self):
        data = self.get("filters/")
        self.assertEqual(data["issuers"][0]["slug"], "iran")
        self.assertIn({"calendar": "solar_hijri", "year": 1373}, data["years"])
        self.assertIn(
            {"value": "bimetal", "label": "بای‌متال (دوفلزی)"}, data["constructions"]
        )

    def test_empty_pack_not_public(self):
        self.item.delete()
        self.assertEqual(self.get("packs/")["count"], 0)
        self.assertEqual(
            self.client.get("/api/coins/packs/pack-1373/").status_code, 404
        )

    def test_write_methods_rejected(self):
        for path in ("", "filters/", "packs/", "250-rial/", "packs/pack-1373/"):
            response = self.client.post("/api/coins/" + path, {}, format="json")
            self.assertEqual(response.status_code, 405)

    def test_list_query_count_bounded(self):
        # Count + page + image query; annotations include existing stock service.
        with self.assertNumQueries(4):
            self.get(in_stock="true")

    def test_out_of_stock_filter_matches_sold_out_offer(self):
        card = self.get(in_stock="false")["results"][0]
        self.assertFalse(card["in_stock"])
        self.assertEqual(card["min_price"], "3000")

    def test_zero_price_cannot_purchase(self):
        self.variant.price = 0
        self.variant.discount_price = None
        self.variant.save()
        self.assertEqual(len(self.get("250-rial/")["issues"]), 2)

    def test_reserved_routes_not_interpreted_as_slugs(self):
        self.assertEqual(self.client.get("/api/coins/filters/").status_code, 200)
        self.assertEqual(self.client.get("/api/coins/packs/").status_code, 200)
        self.assertEqual(self.client.get("/api/coins/does-not-exist/").status_code, 404)

    def test_duplicate_query_keys_rejected(self):
        response = self.client.get(
            "/api/coins/?year=1373&year=1374&calendar=solar_hijri"
        )
        self.assertEqual(response.status_code, 400)

    def test_pack_filters_must_match_one_component(self):
        other_coin = m.CoinType.objects.create(
            name="دیگر",
            slug="other-coin",
            issuer=self.issuer,
            shape="square",
            calendar="solar_hijri",
        )
        other_issue = m.CoinIssue.objects.create(
            coin_type=other_coin, year=1373, calendar="solar_hijri"
        )
        m.CoinPackItem.objects.create(
            pack_variant=self.pv, issue=other_issue, condition_grade="vf"
        )
        publish_fixture(self.pv)
        self.assertEqual(self.get("packs/", shape="square", condition="xf")["count"], 0)
        self.assertEqual(self.get("packs/", shape="square", condition="vf")["count"], 1)

    def test_material_filter_joins_do_not_duplicate_cards(self):
        material = m.CoinMaterial.objects.create(name="مس", slug="copper")
        for part in ("center", "ring"):
            m.CoinCompositionPart.objects.create(
                coin_type=self.coin, material=material, part=part
            )
        self.assertEqual(self.get(material="copper")["count"], 1)
        self.assertEqual(self.get("packs/", material="copper")["count"], 1)

    def test_price_ordering_and_stable_pagination(self):
        coin = m.CoinType.objects.create(
            name="دیگر",
            slug="second",
            issuer=self.issuer,
            calendar="solar_hijri",
            is_published=True,
        )
        issue = m.CoinIssue.objects.create(
            coin_type=coin, year=1373, calendar="solar_hijri"
        )
        product = Product.objects.create(name="دیگر", slug="second", base_price=15000)
        variant = ProductVariant.objects.create(
            product=product, sku="SECOND", price=15000, stock=1
        )
        publish_fixture(m.CoinSpecimen.objects.create(issue=issue, variant=variant))
        data = self.get(ordering="-price", page_size=1)
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["results"][0]["slug"], "second")
        self.assertIsNotNone(data["next"])
        data = self.get(ordering="-price", page_size=1, page=2)
        self.assertEqual(data["results"][0]["slug"], "250-rial")


class IndependentCatalogTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.issuer = m.CoinIssuer.objects.create(name="ایران", slug="iran")
        self.coin = m.CoinType.objects.create(
            name="کاتالوگ مستقل",
            slug="catalog-only",
            issuer=self.issuer,
            is_published=True,
            introduction="معرفی",
            story="## تاریخچه\n\nداستان سکه",
            story_sources="منبع تاریخی",
        )
        self.issue = m.CoinIssue.objects.create(
            coin_type=self.coin, year=2000, description="داستان سال"
        )

    def test_published_catalog_is_public_without_an_offer(self):
        self.assertEqual(self.client.get("/api/coins/").data["count"], 1)
        response = self.client.get("/api/coins/catalog-only/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["issues"][0]["specimens"], [])
        self.assertEqual(len(self.client.get("/api/coins/filters/").data["issuers"]), 1)

    def test_internal_catalog_status_does_not_gate_published_sales(self):
        self.coin.is_published = False
        self.coin.save()
        product = Product.objects.create(name="فروش", slug="sell", base_price=10000)
        variant = ProductVariant.objects.create(
            product=product, sku="SELL", price=10000, stock=0
        )
        specimen = m.CoinSpecimen.objects.create(issue=self.issue, variant=variant)
        self.assertEqual(self.client.get("/api/coins/").data["count"], 0)
        publish_fixture(specimen)
        self.assertEqual(self.client.get("/api/coins/").data["count"], 1)
        data = self.client.get("/api/coins/catalog-only/").data
        self.assertEqual(data["story"], self.coin.story)
        self.assertNotIn("storage_location", str(data))

    def test_issue_image_must_belong_to_type(self):
        from django.core.exceptions import ValidationError

        other = m.CoinType.objects.create(name="دیگر", slug="other", issuer=self.issuer)
        with self.assertRaises(ValidationError):
            m.CoinCatalogImage.objects.create(
                coin_type=other,
                issue=self.issue,
                source_url="https://example.com/image.jpg",
            )
