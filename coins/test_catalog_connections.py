from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from products.models import Product, ProductVariant, ProductVariantImage
from products.services.variant_stock import VariantStockService
from . import models as m
from .services import assert_purchasable
from .api.views import sales


class CatalogConnectionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser('manager', 'm@example.com', 'test')
        self.client.force_login(self.user)
        self.issuer = m.CoinIssuer.objects.create(name='ایران', slug='iran')
        self.coin = m.CoinType.objects.create(name='سکه', issuer=self.issuer, slug='coin', calendar='solar_hijri')
        self.issue = m.CoinIssue.objects.create(coin_type=self.coin, year=1370, calendar='solar_hijri')
        self.product = Product.objects.create(name='سکه بانکی', slug='sale', base_price=1000)
        self.variant = ProductVariant.objects.create(product=self.product, sku='coin-a', price=1000, stock=5)
        ProductVariantImage.objects.create(variant=self.variant, source_url='https://example.com/coin.jpg')

    def url(self, name='connections', **kw):
        return reverse('dashboard:coin_catalog:' + name, kwargs=kw or ({'pk': self.coin.pk} if name == 'connections' else {}))

    def connect(self, variant=None):
        return self.client.post(self.url(), {'action':'connect', 'issue':self.issue.pk, 'variant':(variant or self.variant).pk})

    def test_connect_disconnect_reconnect_preserves_stock(self):
        response = self.connect()
        self.assertEqual(response.status_code, 302)
        link = m.CoinSpecimen.objects.get()
        self.assertTrue(link.catalog_link)
        self.assertTrue(link.is_published)
        self.assertEqual(sales(m.CoinSpecimen.objects.all()).count(), 1)
        assert_purchasable(self.variant, 2)
        self.assertContains(self.client.get(self.url()), 'coin-a')
        response = self.client.post(self.url(), {'action':'disconnect', 'link':link.pk})
        self.assertEqual(response.status_code, 302)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 5)
        self.assertFalse(self.variant.is_sellable)
        self.assertEqual(VariantStockService.calculate(self.variant), 0)
        self.assertEqual(VariantStockService.annotate(ProductVariant.objects.all()).get().available_stock, 0)
        self.assertFalse(sales(m.CoinSpecimen.objects.all()).exists())
        response = self.client.get('/api/coins/coin/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['issues'][0]['specimens'], [])
        with self.assertRaises(ValidationError):
            assert_purchasable(self.variant, 1)
        self.assertEqual(self.connect().status_code, 302)
        self.variant.refresh_from_db()
        self.assertTrue(self.variant.is_sellable)
        self.assertEqual(self.variant.stock, 5)
        self.assertEqual(m.CoinSpecimen.objects.count(), 1)

    def test_multiple_variants_one_coin(self):
        self.connect()
        other = ProductVariant.objects.create(product=self.product, sku='coin-b', price=2000, stock=2)
        ProductVariantImage.objects.create(variant=other, source_url='https://example.com/other.jpg')
        self.assertEqual(self.connect(other).status_code, 302)
        self.assertEqual(m.CoinSpecimen.objects.filter(issue__coin_type=self.coin).count(), 2)

    def test_missing_photo_rolls_back_activation(self):
        self.variant.images.all().delete()
        self.variant.is_sellable = False
        self.variant.save(update_fields=['is_sellable'])
        response = self.connect()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertFalse(m.CoinSpecimen.objects.exists())
        self.variant.refresh_from_db()
        self.assertFalse(self.variant.is_sellable)

    def test_cannot_take_another_catalogs_variant(self):
        self.connect()
        other = m.CoinType.objects.create(name='دیگر', issuer=self.issuer, slug='other')
        issue = m.CoinIssue.objects.create(coin_type=other, year=2000, calendar='gregorian')
        response = self.client.post(self.url(pk=other.pk), {'action':'connect', 'issue':issue.pk, 'variant':self.variant.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(m.CoinSpecimen.objects.get().issue_id, self.issue.pk)

    def test_catalog_form_has_full_details_and_no_sale_fields(self):
        response = self.client.get(self.url('simple-new'))
        self.assertEqual(response.status_code, 200)
        fields = response.context['form'].fields
        self.assertIn('weight_g', fields)
        self.assertIn('diameter_mm', fields)
        self.assertNotIn('for_sale', fields)
        self.assertNotIn('variant', fields)
        data = {'name':'سکه جدید', 'issuer':self.issuer.pk, 'calendar':'gregorian',
                'issue_kind':'circulation', 'construction':'unknown', 'shape':'unknown', 'edge_type':'unknown', 'mint_year':2000}
        response = self.client.post(self.url('simple-new'), data)
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.status_code == 200 else '')
        self.assertEqual(Product.objects.count(), 1)
        self.assertFalse(m.CoinSpecimen.objects.exists())

    def test_permissions_and_csrf(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url(), {"action": "connect"}).status_code, 403)
        user = get_user_model().objects.create_user('staff', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_unrelated_disabled_variant_is_also_blocked(self):
        self.variant.is_sellable = False
        with self.assertRaises(ValidationError):
            assert_purchasable(self.variant, 1)
