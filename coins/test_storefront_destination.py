from django.test import TestCase
from rest_framework import serializers
from products.models import Product, ProductVariant
from products.api.serializers import ProductListSerializer, ProductDetailSerializer, ProductSerializer
from . import models as m
from .testing import publish_fixture
from .storefront import ProductStorefrontMixin


class MinimalProductSerializer(ProductStorefrontMixin, serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "slug")


class StorefrontDestinationTests(TestCase):
    def setUp(self):
        self.issuer = m.CoinIssuer.objects.create(name="ایران", slug="iran")
        self.coin = m.CoinType.objects.create(name="سکه", slug="coin", issuer=self.issuer)
        self.issue = m.CoinIssue.objects.create(coin_type=self.coin, year=2000)
        self.product = Product.objects.create(name="نمونه", slug="sample", base_price=100)
        self.variant = ProductVariant.objects.create(product=self.product, sku="S", price=100, stock=1)
        self.specimen = m.CoinSpecimen.objects.create(issue=self.issue, variant=self.variant)

    def test_unpublished_has_no_special_destination(self):
        self.assertIsNone(MinimalProductSerializer(self.product).data["storefront"])

    def test_all_product_responses_share_coin_identity(self):
        publish_fixture(self.specimen)
        for serializer in (ProductListSerializer, ProductDetailSerializer, ProductSerializer):
            target = serializer(self.product).data["storefront"]
            self.assertEqual(target["kind"], "coin")
            self.assertEqual(target["url"], f"/coins/coin?variant={self.variant.pk}&issue={self.issue.pk}")

    def test_ordinary_product_stays_ordinary(self):
        product = Product.objects.create(name="عادی", slug="normal", base_price=100)
        self.assertIsNone(MinimalProductSerializer(product).data["storefront"])

    def test_card_ignores_unpublished_variant_price_and_stock(self):
        publish_fixture(self.specimen)
        ProductVariant.objects.create(product=self.product, sku="DRAFT", price=1, stock=99)
        data = ProductListSerializer(self.product).data
        self.assertEqual([row["id"] for row in data["variants"]], [self.variant.pk])
        self.assertEqual(int(data["price"]), 100)
        self.assertTrue(data["in_stock"])

    def test_multiple_products_batch_queries_and_variant_mapping(self):
        publish_fixture(self.specimen)
        other = ProductVariant.objects.create(product=self.product, sku="S2", price=100, stock=1)
        second = m.CoinSpecimen.objects.create(issue=self.issue, variant=other)
        publish_fixture(second)
        products = [self.product, Product.objects.create(name="عادی", slug="normal", base_price=100)]
        with self.assertNumQueries(2):
            data = MinimalProductSerializer(products, many=True).data
        self.assertEqual(set(data[0]["storefront"]["variants"]), {str(other.pk), str(self.variant.pk)})
        self.assertIsNone(data[1]["storefront"])

    def test_prepared_pack_uses_pack_destination(self):
        product = Product.objects.create(name="پک", slug="pack", base_price=100)
        variant = ProductVariant.objects.create(product=product, sku="P", price=100, stock=2)
        pack = m.CoinPack.objects.create(product=product, year=2000, calendar=self.issue.calendar, issuer=self.issuer)
        listing = m.CoinPackVariant.objects.create(pack=pack, variant=variant)
        m.CoinPackItem.objects.create(pack_variant=listing, issue=self.issue, quantity=1)
        publish_fixture(listing)
        self.assertEqual(MinimalProductSerializer(product).data["storefront"]["url"], f"/coin-packs/pack?variant={variant.pk}")

    def test_sold_out_keeps_destination_but_inactive_does_not(self):
        publish_fixture(self.specimen)
        ProductVariant.objects.filter(pk=self.variant.pk).update(stock=0)
        self.assertIsNotNone(MinimalProductSerializer(self.product).data["storefront"])
        Product.objects.filter(pk=self.product.pk).update(is_active=False)
        self.assertIsNone(MinimalProductSerializer(self.product).data["storefront"])
