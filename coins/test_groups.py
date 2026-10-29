from importlib import import_module
from unittest import skipUnless
from types import SimpleNamespace
from urllib.parse import urlsplit, parse_qs
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from products.models import Product, ProductVariant
from products.api.serializers import ProductListSerializer
from . import models as m
from .grouping import collapse_products
from .testing import publish_fixture
if apps.is_installed('torob_integration'):
    from torob_integration.models import TorobVariantConfig
    from torob_integration.services.product_mapper import TorobProductMapper
    from torob_integration.services.product_selector import TorobProductSelector


@skipUnless(apps.is_installed('torob_integration'), 'Run with coins.test_group_settings')
class CoinGroupTests(TestCase):
    def setUp(self):
        self.issuer = m.CoinIssuer.objects.create(name='کره جنوبی', slug='kr')
        self.group = m.CoinGroup.objects.create(name='۱۰۰ وون', slug='100-won', issuer=self.issuer,
            story='داستان مشترک', obverse_url='https://example.com/group-front.jpg',
            reverse_url='https://example.com/group-back.jpg')
        self.coins, self.variants, self.links = [], [], []
        for year, price, stock in [(1991, 300, 1), (2002, 500, 2)]:
            coin = m.CoinType.objects.create(name='۱۰۰ وون', slug=f'won-{year}', group=self.group,
                issuer=self.issuer, mint_year=year, is_published=True)
            issue = m.CoinIssue.objects.create(coin_type=coin, year=year)
            product = Product.objects.create(name=f'سال {year}', slug=f'sale-{year}', base_price=price)
            variant = ProductVariant.objects.create(product=product, sku=f'KR-{year}', price=price, stock=stock)
            link = m.CoinSpecimen.objects.create(issue=issue, variant=variant, catalog_link=True,
                sale_mode=m.SaleMode.SIMILAR)
            publish_fixture(link)
            TorobVariantConfig.objects.update_or_create(variant=variant, defaults={'is_enabled': True})
            self.coins.append(coin); self.variants.append(variant); self.links.append(link)

    def test_group_list_one_card_two_years_and_group_images(self):
        data = self.client.get('/api/coins/groups/').json()
        self.assertEqual(data['count'], 1)
        card = data['results'][0]
        self.assertEqual(card['min_price'], '300')
        self.assertTrue(card['in_stock'])
        self.assertEqual(card['image']['url'], self.group.obverse_url)
        self.assertEqual(len(card['images']), 2)
        self.assertTrue(card['is_group'])

    def test_group_detail_shared_story_and_independent_annual_sales(self):
        self.coins[1].year_story = 'ویژه سال ۲۰۰۲'
        self.coins[1].save()
        data = self.client.get('/api/coins/groups/100-won/').json()
        self.assertEqual(data['story'], 'داستان مشترک')
        self.assertEqual([c['mint_year'] for c in data['years']], [1991, 2002])
        self.assertEqual(data['years'][1]['year_story'], 'ویژه سال ۲۰۰۲')
        self.assertEqual(data['years'][1]['issues'][0]['specimens'][0]['variant_id'], self.variants[1].pk)
        self.assertNotEqual(data['years'][0]['issues'][0]['id'], data['years'][1]['issues'][0]['id'])

    def test_unavailable_cheaper_year_does_not_set_available_price(self):
        self.variants[0].stock = 0; self.variants[0].save()
        card = self.client.get('/api/coins/groups/').json()['results'][0]
        self.assertEqual(card['min_price'], '500')
        self.assertTrue(card['in_stock'])

    def test_private_year_does_not_leak_into_group(self):
        self.links[1].is_published = False; self.links[1].save()
        self.coins[1].is_published = False; self.coins[1].save()
        data = self.client.get('/api/coins/groups/100-won/').json()
        self.assertEqual(len(data['years']), 1)
        self.assertEqual(data['years'][0]['mint_year'], 1991)

    def test_empty_private_group_is_404(self):
        group = m.CoinGroup.objects.create(name='private', slug='private', issuer=self.issuer)
        self.assertEqual(self.client.get('/api/coins/groups/private/').status_code, 404)

    def test_catalog_only_group_has_no_price(self):
        for link in self.links:
            link.is_published = False; link.save()
        card = self.client.get('/api/coins/groups/').json()['results'][0]
        self.assertIsNone(card['min_price']); self.assertFalse(card['in_stock'])

    def test_year_filter_applies_before_group_aggregation(self):
        data = self.client.get('/api/coins/groups/?year=2002&calendar=gregorian').json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['min_price'], '500')

    def test_product_list_collapses_before_pagination_and_respects_filtered_subset(self):
        normal = Product.objects.create(name='normal', slug='normal', base_price=20)
        products = Product.objects.filter(pk__in=[v.product_id for v in self.variants] + [normal.pk])
        collapsed = collapse_products(products)
        self.assertEqual(collapsed.count(), 2)
        one_year = collapse_products(products.filter(pk=self.variants[1].product_id))
        self.assertEqual(list(one_year.values_list('pk', flat=True)), [self.variants[1].product_id])
        searched = self.client.get('/api/products/', {'search': self.group.name}).json()
        self.assertEqual(searched['count'], 1)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        rows = response.json().get('data', [])
        self.assertEqual(sum(bool(row.get('storefront', {}).get('is_group')) for row in rows if row.get('storefront')), 1)

    def test_storefront_group_card_and_deep_variant_mapping(self):
        data = ProductListSerializer(self.variants[1].product).data
        target = data['storefront']
        self.assertEqual(target['url'], '/coins/groups/100-won')
        self.assertEqual(data['thumb'], self.group.obverse_url)
        self.assertEqual(data['price'], '300')
        query = parse_qs(urlsplit(target['variants'][str(self.variants[1].pk)]).query)
        self.assertEqual(query['variant'], [str(self.variants[1].pk)])
        self.assertEqual(query['coin'], ['won-2002'])

    def test_torob_keeps_unique_variant_exact_price_and_annual_selection(self):
        rows = list(TorobProductSelector.base_queryset().order_by('pk'))
        self.assertEqual(len(rows), 2)
        mapped = [TorobProductMapper.map_variant(v) for v in rows]
        self.assertEqual([r['page_unique'] for r in mapped], [str(v.pk) for v in self.variants])
        self.assertEqual([r['current_price'] for r in mapped], [300, 500])
        self.assertEqual(mapped[0]['product_group_id'], mapped[1]['product_group_id'])
        self.assertEqual(self.variants[1].torob_config.product_group_id, mapped[1]['product_group_id'])
        self.assertIn('2002', mapped[1]['title'])
        self.assertEqual(mapped[1]['spec']['سال ضرب'], 2002)
        query = parse_qs(urlsplit(mapped[1]['page_url']).query)
        self.assertEqual(query['variant'], [str(self.variants[1].pk)])
        self.assertEqual(query['coin'], ['won-2002'])
        self.assertNotEqual(mapped[1]['image_links'][0], self.group.obverse_url)
        self.assertEqual(list(TorobProductSelector.get_by_page_urls([mapped[1]['page_url']]).values_list('pk', flat=True)), [self.variants[1].pk])

    def test_torob_hides_disconnected_listing_and_group_edit_touches_config(self):
        config = self.variants[1].torob_config
        old = config.torob_updated_at
        self.group.story = 'داستان تازه'; self.group.save()
        config.refresh_from_db(); self.assertGreater(config.torob_updated_at, old)
        self.links[1].is_published = False; self.links[1].save()
        self.assertFalse(TorobProductSelector.base_queryset().filter(pk=self.variants[1].pk).exists())

    def test_group_rejects_incompatible_country(self):
        other = m.CoinIssuer.objects.create(name='other', slug='other')
        self.coins[0].issuer = other
        with self.assertRaises(ValidationError): self.coins[0].save()

    def test_group_dashboard_edit_shared_content(self):
        user = get_user_model().objects.create_superuser('group-admin', 'g@example.com', 'test')
        self.client.force_login(user)
        response = self.client.post(f'/dashboard/coins/records/group/{self.group.pk}/edit/', {
            'name': self.group.name, 'issuer': self.issuer.pk, 'story': 'داستان یک‌بار ویرایش‌شده',
            'obverse_url': self.group.obverse_url, 'reverse_url': self.group.reverse_url,
        })
        self.assertEqual(response.status_code, 302)
        self.group.refresh_from_db(); self.assertEqual(self.group.story, 'داستان یک‌بار ویرایش‌شده')
        self.assertEqual(len(self.client.get('/api/coins/groups/100-won/').json()['years']), 2)

    def test_migration_preserves_conflicting_annual_text_and_variant_ids(self):
        for index, coin in enumerate(self.coins):
            m.CoinType.objects.filter(pk=coin.pk).update(group=None, story=f'متن {index}')
        migrate = import_module('coins.migrations.0007_populate_coin_groups')
        migrate.populate(apps, SimpleNamespace(connection=connection))
        for index, coin in enumerate(self.coins):
            coin.refresh_from_db()
            self.assertEqual(coin.story, f'متن {index}')
            self.assertEqual(coin.year_story, f'متن {index}')
            self.assertEqual(coin.issues.get().specimens.get().variant_id, self.variants[index].pk)
        self.assertEqual(self.coins[0].group_id, self.coins[1].group_id)

    def test_torob_group_reference_fallback_is_absolute_without_request(self):
        self.variants[0].images.all().delete()
        self.group.obverse = 'coins/groups/front.jpg'
        self.group.save()
        links = TorobProductMapper.get_image_links(self.variants[0])
        self.assertTrue(links[0].startswith('https://'))
        self.assertIn('/media/coins/groups/front.jpg', links[0])

    def test_migration_common_story_is_shared_without_erasing_archived_text(self):
        for coin in self.coins:
            m.CoinType.objects.filter(pk=coin.pk).update(group=None, story='یک متن مشترک')
        migrate = import_module('coins.migrations.0007_populate_coin_groups')
        migrate.populate(apps, SimpleNamespace(connection=connection))
        self.coins[0].refresh_from_db()
        group = self.coins[0].group
        self.assertEqual(group.story, 'یک متن مشترک')
        group.story = 'ویرایش مشترک'; group.save()
        data = self.client.get('/api/coins/groups/' + group.slug + '/').json()
        self.assertEqual(data['story'], 'ویرایش مشترک')
        self.assertTrue(all(c['year_story'] == '' for c in data['years']))
        for coin in self.coins:
            coin.refresh_from_db(); self.assertEqual(coin.story, 'یک متن مشترک')
