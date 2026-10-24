from io import BytesIO
from tempfile import TemporaryDirectory
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from inventory.models import InventoryLot, InventoryMovement
from products.models import Product, ProductVariantImage
from . import models as m


class SimpleWorkflowTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        settings = override_settings(MEDIA_ROOT=self.media.name)
        settings.enable()
        self.addCleanup(settings.disable)
        self.user = get_user_model().objects.create_superuser('manager','m@example.com','test')
        self.client.force_login(self.user)
        self.issuer = m.CoinIssuer.objects.create(name='ژاپن', slug='japan')

    def url(self, name, **kw):
        return reverse('dashboard:coin_catalog:'+name, kwargs=kw)

    def photo(self):
        b = BytesIO()
        Image.new('RGB', (8,8)).save(b, 'JPEG')
        return SimpleUploadedFile('coin.jpg', b.getvalue(), content_type='image/jpeg')

    def data(self, **kw):
        return dict(name='۱۰ ین', issuer=self.issuer.pk, calendar='gregorian', year=2000, **kw)

    def create_sale(self, **kw):
        r = self.client.post(self.url('simple-new'), self.data(for_sale='on', price=20000,
            sale_mode='unique', actual_photos='on', obverse=self.photo(), reverse=self.photo(), **kw))
        self.assertEqual(r.status_code,302, r.context['form'].errors if r.status_code==200 else '')
        return m.CoinSpecimen.objects.get()

    def test_catalog_only_needs_no_sale_records(self):
        r = self.client.post(self.url('simple-new'), self.data())
        self.assertEqual(r.status_code,302)
        self.assertEqual(m.CoinIssue.objects.get().year,2000)
        self.assertFalse(Product.objects.exists())

    def test_photos_parent_stock_and_publish(self):
        listing = self.create_sale(quantity=1, unit_cost=12000)
        self.assertFalse(listing.is_published)
        self.assertEqual(listing.variant.stock,1)
        self.assertEqual(InventoryLot.objects.get().quantity_remaining,1)
        self.assertEqual(InventoryMovement.objects.get().quantity,1)
        self.assertEqual(m.CoinImageDetail.objects.count(),2)
        self.assertEqual(set(m.CoinCatalogImage.objects.values_list('image',flat=True)),
            set(ProductVariantImage.objects.values_list('image',flat=True)))
        url = self.url('simple-sale',kind='coin',pk=listing.pk)
        self.assertContains(self.client.get(url),'پیش‌نویس فروش')
        r = self.client.post(url, {'price':20000, 'action':'publish'})
        self.assertEqual(r.status_code,302)
        listing.refresh_from_db()
        self.assertTrue(listing.is_published)

    def test_missing_photos_allow_draft_but_publish_rolls_back_stock(self):
        r = self.client.post(self.url('simple-new'),self.data(for_sale='on',price=100,sale_mode='unique'))
        self.assertEqual(r.status_code,302)
        listing = m.CoinSpecimen.objects.get()
        r = self.client.post(self.url('simple-sale',kind='coin',pk=listing.pk),
            {'price':200,'quantity':1,'unit_cost':50,'action':'publish'})
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.context['form'].errors)
        listing.variant.refresh_from_db()
        self.assertEqual(listing.variant.stock,0)
        self.assertEqual(listing.variant.price,100)
        self.assertFalse(InventoryLot.objects.exists())

    def test_unique_restock_is_atomic(self):
        listing = self.create_sale(quantity=1,unit_cost=50)
        r = self.client.post(self.url('simple-sale',kind='coin',pk=listing.pk),
            {'price':20000,'quantity':1,'unit_cost':50,'action':'save'})
        self.assertEqual(r.status_code,200)
        self.assertEqual(InventoryLot.objects.count(),1)
        listing.variant.refresh_from_db()
        self.assertEqual(listing.variant.stock,1)

    def test_existing_catalog_reuses_photos_without_uploading_again(self):
        self.client.post(self.url('simple-new'),self.data(obverse=self.photo(),reverse=self.photo()))
        coin = m.CoinType.objects.get()
        r=self.client.post(self.url('simple-new'),dict(existing=coin.pk, calendar='gregorian',
            for_sale='on', price=100, sale_mode='unique', actual_photos='on'))
        self.assertEqual(r.status_code,302)
        self.assertEqual(m.CoinType.objects.count(),1)
        self.assertEqual(m.CoinCatalogImage.objects.count(),2)
        self.assertEqual(m.CoinImageDetail.objects.count(),2)

    def test_new_pack_and_images_share_one_form(self):
        self.client.post(self.url('simple-new'),self.data())
        issue=m.CoinIssue.objects.get()
        d=dict(name='پک ژاپن',year=2000,calendar='gregorian',issuer=self.issuer.pk,
            price=1000,sale_mode='similar',quantity=2,unit_cost=500,photo=self.photo(),
            **{'items-TOTAL_FORMS':1,'items-INITIAL_FORMS':0,'items-0-issue':issue.pk,
               'items-0-quantity':1})
        r=self.client.post(self.url('simple-pack'),d)
        self.assertEqual(r.status_code,302, r.context['form'].errors if r.status_code==200 else '')
        listing=m.CoinPackVariant.objects.get()
        r=self.client.post(self.url('simple-sale',kind='pack',pk=listing.pk),{'price':1000,'action':'publish'})
        self.assertEqual(r.status_code,302)
        self.assertEqual(listing.variant.stock,2)
        self.assertEqual(listing.items.count(),1)

    def test_unauthorized_staff_cannot_register(self):
        staff=get_user_model().objects.create_user('staff',password='test',is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.post(self.url('simple-new'),self.data()).status_code,403)
        self.assertEqual(self.client.get(self.url('simple-pack')).status_code,403)

    def test_edit_preserves_specialist_fields(self):
        coin=m.CoinType.objects.create(name='سکه',slug='coin',issuer=self.issuer,weight_g='4.2')
        r=self.client.post(self.url('simple-edit',pk=coin.pk),self.data(story='داستان تازه'))
        self.assertEqual(r.status_code,302)
        coin.refresh_from_db()
        self.assertEqual(coin.story,'داستان تازه')
        self.assertAlmostEqual(float(coin.weight_g),4.2)

    def test_sales_workspace_includes_existing_listing(self):
        listing = self.create_sale()
        self.assertContains(self.client.get(self.url('simple-sales')), 'قیمت، عکس، موجودی و انتشار')
        self.assertContains(self.client.get(self.url('simple-sales'), {'q':'missing'}), 'هنوز فروش ثبت نشده است.')

    def test_delete_sale_photo_keeps_shared_catalog_file_and_stops_sale(self):
        from products.signals import files  # production receiver, also in isolated tests
        listing=self.create_sale()
        url=self.url('simple-sale',kind='coin',pk=listing.pk)
        self.client.post(url, {'price':20000,'action':'publish'})
        photo=listing.variant.images.get(coin_detail__view_type='obverse')
        storage,name=photo.image.storage,photo.image.name
        delete=self.url('simple-delete-photo',kind='coin',pk=listing.pk,photo_pk=photo.pk)
        self.assertEqual(self.client.get(delete).status_code,405)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.client.post(delete).status_code,302)
        self.assertFalse(ProductVariantImage.objects.filter(pk=photo.pk).exists())
        self.assertTrue(storage.exists(name))
        self.assertEqual(m.CoinCatalogImage.objects.count(),2)
        listing.refresh_from_db()
        self.assertFalse(listing.is_published)
        self.assertTrue(listing.variant.images.get().is_main)

    def test_delete_catalog_photo_keeps_sale_then_cleans_last_reference(self):
        listing=self.create_sale()
        ref=m.CoinCatalogImage.objects.get(view_type='obverse')
        name,storage=ref.image.name,ref.image.storage
        with self.captureOnCommitCallbacks(execute=True):
            r=self.client.post(self.url('simple-delete-photo',kind='catalog',pk=ref.coin_type_id,photo_pk=ref.pk))
        self.assertEqual(r.status_code,302)
        self.assertTrue(storage.exists(name))
        photo=listing.variant.images.get(coin_detail__view_type='obverse')
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url('simple-delete-photo',kind='coin',pk=listing.pk,photo_pk=photo.pk))
        self.assertFalse(storage.exists(name))

    def test_delete_cannot_target_other_listing_photo(self):
        listing=self.create_sale()
        other=m.CoinType.objects.create(name='دیگر',slug='other',issuer=self.issuer)
        ref=m.CoinCatalogImage.objects.get(view_type='obverse')
        r=self.client.post(self.url('simple-delete-photo',kind='catalog',pk=other.pk,photo_pk=ref.pk))
        self.assertEqual(r.status_code,404)
        self.assertTrue(m.CoinCatalogImage.objects.filter(pk=ref.pk).exists())

    def test_delete_needs_delete_permission_and_csrf(self):
        from django.contrib.auth.models import Permission
        from django.test import Client
        listing=self.create_sale()
        photo=listing.variant.images.first()
        url=self.url('simple-delete-photo',kind='coin',pk=listing.pk,photo_pk=photo.pk)
        c=Client(enforce_csrf_checks=True)
        c.force_login(self.user)
        self.assertEqual(c.post(url).status_code,403)
        staff=get_user_model().objects.create_user('editor',is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='change_coinspecimen'))
        self.client.force_login(staff)
        self.assertEqual(self.client.post(url).status_code,403)
        self.assertTrue(ProductVariantImage.objects.filter(pk=photo.pk).exists())
