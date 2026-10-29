from importlib import import_module
from io import BytesIO
from tempfile import TemporaryDirectory
from PIL import Image
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse
from products.models import Product, ProductVariant
from . import models as m


class YearCatalogTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        override = override_settings(MEDIA_ROOT=self.media.name)
        override.enable()
        self.addCleanup(override.disable)
        self.user = get_user_model().objects.create_superuser('annual', 'annual@example.com', 'test')
        self.client.force_login(self.user)
        self.issuer = m.CoinIssuer.objects.create(name='ایران', slug='iran')

    def data(self, year, **kwargs):
        data = dict(name='۲۵۰ ریالی', issuer=self.issuer.pk, mint_year=year,
                    calendar='solar_hijri', issue_kind='circulation', construction='unknown',
                    shape='unknown', edge_type='unknown', is_published='on', weight_g='4.2')
        data.update(kwargs)
        return data

    def photo(self, color):
        output = BytesIO()
        Image.new('RGB', (8,8), color=color).save(output, 'JPEG')
        return SimpleUploadedFile('coin.jpg', output.getvalue(), content_type='image/jpeg')

    def new_url(self):
        return reverse('dashboard:coin_catalog:simple-new')

    def test_years_have_separate_pages_images_and_issue(self):
        for year, color in ((1373, 'red'), (1374, 'blue')):
            response = self.client.post(self.new_url(), self.data(year, obverse=self.photo(color)))
            self.assertEqual(response.status_code, 302)
        coins = list(m.CoinType.objects.order_by('mint_year'))
        self.assertEqual([c.mint_year for c in coins], [1373,1374])
        self.assertNotEqual(coins[0].slug, coins[1].slug)
        self.assertNotEqual(coins[0].catalog_images.get().image.name, coins[1].catalog_images.get().image.name)
        for coin in coins:
            self.assertEqual(coin.issues.get().year, coin.mint_year)
            response = self.client.get('/api/coins/' + coin.slug + '/')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['mint_year'],coin.mint_year)
            self.assertEqual(len(response.json()['images']),1)
        card = self.client.get('/api/coins/').json()
        self.assertEqual(card['count'],2)

    def test_copy_for_new_year_keeps_specs_but_no_images_or_sales(self):
        self.client.post(self.new_url(), self.data(1373, obverse=self.photo('red')))
        source = m.CoinType.objects.get()
        product = Product.objects.create(name='سکه',slug='sale',base_price=100)
        variant = ProductVariant.objects.create(product=product,sku='annual',price=100)
        m.CoinSpecimen.objects.create(issue=source.issues.get(),variant=variant)
        url = self.new_url() + '?copy=' + str(source.pk)
        response = self.client.get(url)
        self.assertEqual(response.context['form'].initial['weight_g'],source.weight_g)
        self.assertNotIn('mint_year',response.context['form'].initial)
        self.assertFalse(response.context['form'].initial['is_published'])
        self.assertContains(response,'عکس‌ها و اتصال‌های فروش کپی نمی‌شوند')
        response = self.client.post(url,self.data(1374))
        self.assertEqual(response.status_code,302)
        target = m.CoinType.objects.exclude(pk=source.pk).get()
        self.assertEqual(target.mint_year,1374)
        self.assertFalse(target.catalog_images.exists())
        self.assertFalse(m.CoinSpecimen.objects.filter(issue__coin_type=target).exists())
        self.assertEqual(m.CoinSpecimen.objects.get().variant_id,variant.pk)

    def test_other_year_rejected_under_same_catalog(self):
        self.client.post(self.new_url(),self.data(1373))
        coin = m.CoinType.objects.get()
        with self.assertRaises(ValidationError):
            m.CoinIssue.objects.create(coin_type=coin, year=1374, calendar=coin.calendar)
        coin.mint_year = 1374
        with self.assertRaises(ValidationError):
            coin.save()

    def test_missing_year_does_not_create_records(self):
        response = self.client.post(self.new_url(),self.data(''))
        self.assertEqual(response.status_code,200)
        self.assertIn('mint_year',response.context['form'].errors)
        self.assertFalse(m.CoinType.objects.exists())

    def test_connections_infer_year_without_second_selection(self):
        self.client.post(self.new_url(),self.data(1373))
        coin = m.CoinType.objects.get()
        from .catalog_forms import VariantConnectionForm
        form = VariantConnectionForm({'variant':'0'},coin=coin)
        self.assertTrue(form.fields['issue'].widget.is_hidden)
        self.assertEqual(int(form.data['issue']),coin.issues.get().pk)


class SplitExistingYearTests(TestCase):
    def test_split_preserves_issues_variants_and_year_specific_images(self):
        issuer = m.CoinIssuer.objects.create(name='ایران',slug='migration-iran')
        coin = m.CoinType.objects.create(name='سکه قدیمی',slug='old-coin',issuer=issuer,weight_g='4.2')
        issues = [m.CoinIssue.objects.create(coin_type=coin,year=year) for year in (2000,2001)]
        product = Product.objects.create(name='کالا',slug='migrate-sale',base_price=100)
        variant = ProductVariant.objects.create(product=product,sku='migrate',price=100,stock=3)
        link = m.CoinSpecimen.objects.create(issue=issues[1],variant=variant,sale_mode='similar')
        shared = m.CoinCatalogImage.objects.create(coin_type=coin,source_url='https://example.com/shared.jpg')
        photo = m.CoinCatalogImage.objects.create(coin_type=coin,issue=issues[1],source_url='https://example.com/2001.jpg')
        reference = m.CoinCatalogReference.objects.create(coin_type=coin,catalog='KM',number='10')
        migration = import_module('coins.migrations.0005_cointype_mint_year')
        # Historical models avoid runtime validation/signals, just like real migrate.
        from django.db.migrations.executor import MigrationExecutor
        state = MigrationExecutor(connection).loader.project_state([('coins','0005_cointype_mint_year')])
        class Editor:
            connection = connection
        migration.separate_years(state.apps,Editor())
        coin.refresh_from_db(); link.refresh_from_db(); photo.refresh_from_db(); variant.refresh_from_db()
        other = m.CoinType.objects.exclude(pk=coin.pk).get()
        self.assertEqual(coin.mint_year,2000)
        self.assertEqual(other.mint_year,2001)
        self.assertEqual(link.issue_id,issues[1].pk)
        self.assertEqual(link.variant_id,variant.pk)
        self.assertEqual(link.issue.coin_type_id,other.pk)
        self.assertEqual(photo.coin_type_id,other.pk)
        self.assertEqual(other.references.get().number,reference.number)
        self.assertEqual(other.catalog_images.get(issue__isnull=True).source_url,shared.source_url)
        self.assertEqual(variant.stock,3)
        self.assertEqual(m.CoinSpecimen.objects.count(),1)
