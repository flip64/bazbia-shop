from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from products.models import Product, ProductVariant, ProductVariantImage
from . import models as m


class VariantPhotoTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            "manager", "test@example.com", "test"
        )
        self.client.force_login(self.user)
        p = Product.objects.create(name="سکه", slug="coin", base_price=1000)
        self.variant = ProductVariant.objects.create(product=p, sku="COIN", price=1000)
        issuer = m.CoinIssuer.objects.create(name="ایران", slug="iran")
        coin = m.CoinType.objects.create(name="سکه", slug="coin", issuer=issuer)
        issue = m.CoinIssue.objects.create(coin_type=coin, year=2000)
        self.sample = m.CoinSpecimen.objects.create(issue=issue, variant=self.variant)
        self.url = reverse(
            "dashboard:coin_catalog:create", kwargs={"kind": "variant-image"}
        )

    def test_prefill_variant_and_include_linked_variant_in_lookup(self):
        response = self.client.get(self.url, {"variant": self.variant.pk})
        self.assertContains(response, "COIN")
        self.assertEqual(
            int(response.context["form"]["variant"].value()), self.variant.pk
        )
        response = self.client.get(
            reverse("dashboard:coin_catalog:variant-lookup"),
            {"kind": "variant-image", "q": "COIN"},
        )
        self.assertEqual(response.json()["results"][0]["id"], self.variant.pk)

    def test_photo_and_side_saved_together(self):
        response = self.client.post(
            self.url,
            {
                "variant": self.variant.pk,
                "source_url": "https://example.com/obverse.jpg",
                "view_type": "obverse",
                "caption": "رو",
            },
        )
        self.assertEqual(response.status_code, 302)
        image = ProductVariantImage.objects.get()
        self.assertEqual(image.variant_id, self.variant.pk)
        self.assertEqual(image.coin_detail.view_type, "obverse")
        self.assertEqual(image.coin_detail.caption, "رو")

    def test_empty_photo_rejected_without_creating_records(self):
        response = self.client.post(
            self.url, {"variant": self.variant.pk, "view_type": "obverse"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ProductVariantImage.objects.exists())
        self.assertFalse(m.CoinImageDetail.objects.exists())

    def test_existing_sample_has_direct_photo_link(self):
        response = self.client.get(
            reverse(
                "dashboard:coin_catalog:record-detail",
                kwargs={"kind": "specimen", "pk": self.sample.pk},
            )
        )
        self.assertContains(response, "بارگذاری عکس رو یا پشت این واریانت")

    def test_upload_file_and_side_together(self):
        from io import BytesIO
        from tempfile import TemporaryDirectory
        from django.test import override_settings
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        data = BytesIO()
        Image.new("RGB", (20, 20)).save(data, format="PNG")
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response = self.client.post(
                self.url,
                {
                    "variant": self.variant.pk,
                    "image": SimpleUploadedFile(
                        "coin.png", data.getvalue(), content_type="image/png"
                    ),
                    "view_type": "reverse",
                },
            )
            self.assertEqual(response.status_code, 302)
            image = ProductVariantImage.objects.get()
            self.assertTrue(image.image.storage.exists(image.image.name))
            self.assertEqual(image.coin_detail.view_type, "reverse")
