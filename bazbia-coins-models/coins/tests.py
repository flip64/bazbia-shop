from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from products.models import Product, ProductVariant, ProductVariantImage
from .models import (
    Calendar,
    CoinIssuer,
    HistoricalPeriod,
    CoinCurrency,
    CoinType,
    CoinIssue,
    CoinMaterial,
    CoinCompositionPart,
    CoinCatalogReference,
    CoinSpecimen,
    CoinPack,
    CoinPackVariant,
    CoinPackItem,
    CoinImageDetail,
    SaleMode,
    Finish,
)


class CoinModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.issuer = CoinIssuer.objects.create(name="ایران", slug="iran")
        cls.other = CoinIssuer.objects.create(name="کانادا", slug="canada")
        cls.period = HistoricalPeriod.objects.create(
            name="دوره نمونه", slug="period", issuer=cls.issuer
        )
        cls.coin = CoinType.objects.create(
            name="۲۵۰ ریالی",
            slug="250-rials",
            issuer=cls.issuer,
            period=cls.period,
            calendar=Calendar.SOLAR_HIJRI,
            year_start=1372,
            year_end=1382,
            construction=CoinType.Construction.BIMETAL,
        )
        cls.issue = CoinIssue.objects.create(
            coin_type=cls.coin, year=1373, calendar=Calendar.SOLAR_HIJRI
        )
        cls.product = Product.objects.create(
            name="پک سال ۱۳۷۳", slug="pack-1373", base_price=100000
        )
        cls.variant = ProductVariant.objects.create(
            product=cls.product, sku="PACK-1373", price=100000, stock=3
        )
        cls.pack = CoinPack.objects.create(
            product=cls.product,
            year=1373,
            calendar=Calendar.SOLAR_HIJRI,
            issuer=cls.issuer,
        )
        cls.pv = CoinPackVariant.objects.create(pack=cls.pack, variant=cls.variant)

    def loose_variant(self, stock=1):
        product = Product.objects.create(
            name="سکه تکی", slug="single", base_price=20000
        )
        return ProductVariant.objects.create(
            product=product, sku="SINGLE", price=20000, stock=stock
        )

    def test_prepared_pack_contents_do_not_consume_stock(self):
        item = CoinPackItem.objects.create(
            pack_variant=self.pv, issue=self.issue, quantity=2
        )
        self.assertEqual(self.pv.coin_count, 2)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)
        self.assertEqual(item.quantity, 2)

    def test_wrong_year_rejected(self):
        issue = CoinIssue.objects.create(
            coin_type=self.coin, year=1374, calendar=Calendar.SOLAR_HIJRI
        )
        with self.assertRaises(ValidationError):
            CoinPackItem.objects.create(pack_variant=self.pv, issue=issue)

    def test_wrong_calendar_rejected(self):
        coin = CoinType.objects.create(name="دیگر", slug="other", issuer=self.issuer)
        issue = CoinIssue.objects.create(coin_type=coin, year=1373)
        with self.assertRaises(ValidationError):
            CoinPackItem.objects.create(pack_variant=self.pv, issue=issue)

    def test_wrong_country_rejected(self):
        coin = CoinType.objects.create(
            name="خارجی",
            slug="foreign",
            issuer=self.other,
            calendar=Calendar.SOLAR_HIJRI,
        )
        issue = CoinIssue.objects.create(
            coin_type=coin, year=1373, calendar=Calendar.SOLAR_HIJRI
        )
        with self.assertRaises(ValidationError):
            CoinPackItem.objects.create(pack_variant=self.pv, issue=issue)

    def test_multicountry_pack(self):
        self.pack.issuer = None
        self.pack.save()
        coin = CoinType.objects.create(
            name="خارجی",
            slug="foreign",
            issuer=self.other,
            calendar=Calendar.SOLAR_HIJRI,
        )
        issue = CoinIssue.objects.create(
            coin_type=coin, year=1373, calendar=Calendar.SOLAR_HIJRI
        )
        CoinPackItem.objects.create(pack_variant=self.pv, issue=issue)

    def test_pack_cannot_change_year_behind_items(self):
        CoinPackItem.objects.create(pack_variant=self.pv, issue=self.issue)
        self.pack.year = 1374
        with self.assertRaises(ValidationError):
            self.pack.save()

    def test_issue_cannot_change_year_behind_pack(self):
        CoinPackItem.objects.create(pack_variant=self.pv, issue=self.issue)
        self.issue.year = 1374
        with self.assertRaises(ValidationError):
            self.issue.save()

    def test_zero_count_rejected_at_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CoinPackItem.objects.bulk_create(
                [CoinPackItem(pack_variant=self.pv, issue=self.issue, quantity=0)]
            )

    def test_duplicate_pack_item_rejected(self):
        CoinPackItem.objects.create(pack_variant=self.pv, issue=self.issue)
        with self.assertRaises(ValidationError):
            CoinPackItem.objects.create(pack_variant=self.pv, issue=self.issue)

    def test_pack_variants_have_independent_contents(self):
        other = ProductVariant.objects.create(
            product=self.product, sku="PACK-SECOND", price=110000, stock=1
        )
        pv = CoinPackVariant.objects.create(
            pack=self.pack, variant=other, sale_mode=SaleMode.UNIQUE
        )
        CoinPackItem.objects.create(pack_variant=self.pv, issue=self.issue, quantity=2)
        CoinPackItem.objects.create(pack_variant=pv, issue=self.issue, quantity=1)
        self.assertEqual(pv.coin_count, 1)
        self.assertEqual(self.pv.coin_count, 2)

    def test_variant_must_belong_to_pack_product(self):
        with self.assertRaises(ValidationError):
            CoinPackVariant.objects.create(pack=self.pack, variant=self.loose_variant())

    def test_single_coin_cannot_use_pack_variant(self):
        with self.assertRaises(ValidationError):
            CoinSpecimen.objects.create(
                issue=self.issue, variant=self.variant, sale_mode=SaleMode.SIMILAR
            )

    def test_unique_specimen_max_one(self):
        with self.assertRaises(ValidationError):
            CoinSpecimen.objects.create(
                issue=self.issue, variant=self.loose_variant(stock=2)
            )

    def test_similar_specimens_allowed(self):
        specimen = CoinSpecimen.objects.create(
            issue=self.issue,
            variant=self.loose_variant(stock=5),
            sale_mode=SaleMode.SIMILAR,
        )
        self.assertEqual(specimen.variant.stock, 5)

    def test_certificate_requires_company(self):
        with self.assertRaises(ValidationError):
            CoinSpecimen.objects.create(
                issue=self.issue,
                variant=self.loose_variant(),
                certification_number="123",
            )

    def test_unknown_damage_preserved(self):
        specimen = CoinSpecimen.objects.create(
            issue=self.issue, variant=self.loose_variant()
        )
        self.assertIsNone(specimen.cleaned)
        self.assertIsNone(specimen.corroded)

    def test_undated_issue_and_known_date_rules(self):
        undated = CoinIssue.objects.create(
            coin_type=self.coin,
            calendar=Calendar.SOLAR_HIJRI,
            date_status=CoinIssue.DateStatus.UNDATED,
        )
        self.assertIsNone(undated.year)
        with self.assertRaises(ValidationError):
            CoinPackItem.objects.create(pack_variant=self.pv, issue=undated)
        with self.assertRaises(ValidationError):
            CoinIssue.objects.create(coin_type=self.coin, calendar=Calendar.SOLAR_HIJRI)

    def test_non_gregorian_equivalent_is_range(self):
        self.issue.gregorian_year_start = 1994
        self.issue.gregorian_year_end = 1995
        self.issue.save()
        self.issue.gregorian_year_end = 1993
        with self.assertRaises(ValidationError):
            self.issue.save()

    def test_year_outside_type_range(self):
        with self.assertRaises(ValidationError):
            CoinIssue.objects.create(
                coin_type=self.coin, calendar=Calendar.SOLAR_HIJRI, year=1370
            )

    def test_period_must_match_issuer(self):
        with self.assertRaises(ValidationError):
            CoinType.objects.create(
                name="بد", slug="bad", issuer=self.other, period=self.period
            )

    def test_period_cycle_rejected(self):
        child = HistoricalPeriod.objects.create(
            name="فرزند", slug="child", issuer=self.issuer, parent=self.period
        )
        self.period.parent = child
        with self.assertRaises(ValidationError):
            self.period.save()

    def test_shared_currency_allowed(self):
        currency = CoinCurrency.objects.create(name="پول مشترک", slug="shared")
        currency.issuers.add(self.issuer, self.other)
        self.coin.currency = currency
        self.coin.save()
        self.assertEqual(currency.issuers.count(), 2)

    def test_complete_pack_requires_definition(self):
        self.pack.is_complete = True
        with self.assertRaises(ValidationError):
            self.pack.save()
        self.pack.completeness_scope = "تمام ارزش‌های اسمی رایج، بدون گونه‌های ضرب"
        self.pack.save()

    def test_reference_has_exactly_one_target(self):
        with self.assertRaises(ValidationError):
            CoinCatalogReference.objects.create(catalog="KM", number="1")
        with self.assertRaises(ValidationError):
            CoinCatalogReference.objects.create(
                catalog="KM", number="1", coin_type=self.coin, issue=self.issue
            )
        CoinCatalogReference.objects.create(
            catalog="KM", number="1", coin_type=self.coin
        )

    def test_bimetal_parts_and_fineness(self):
        material = CoinMaterial.objects.create(name="نقره", slug="silver")
        CoinCompositionPart.objects.create(
            coin_type=self.coin,
            part="center",
            material=material,
            fineness=Decimal("0.925"),
        )
        CoinCompositionPart.objects.create(
            coin_type=self.coin, part="ring", material=material
        )
        with self.assertRaises(ValidationError):
            CoinCompositionPart.objects.create(
                coin_type=self.coin,
                part="coating",
                material=material,
                fineness=Decimal("1.1"),
            )

    def test_negative_measurement_rejected(self):
        self.coin.weight_g = Decimal("-1")
        with self.assertRaises(ValidationError):
            self.coin.save()

    def test_proof_is_separate_from_condition(self):
        self.issue.finish = Finish.PROOF
        self.issue.save()
        specimen = CoinSpecimen.objects.create(
            issue=self.issue, variant=self.loose_variant(), scratched=True
        )
        self.assertEqual(specimen.issue.finish, Finish.PROOF)
        self.assertTrue(specimen.scratched)

    def test_image_matches_pack_component(self):
        item = CoinPackItem.objects.create(pack_variant=self.pv, issue=self.issue)
        image = ProductVariantImage.objects.create(
            variant=self.variant, source_url="https://example.com/pack.jpg"
        )
        CoinImageDetail.objects.create(image=image, view_type="obverse", pack_item=item)
        loose = self.loose_variant()
        CoinSpecimen.objects.create(issue=self.issue, variant=loose)
        another_image = ProductVariantImage.objects.create(variant=loose)
        with self.assertRaises(ValidationError):
            CoinImageDetail.objects.create(
                image=another_image, view_type="obverse", pack_item=item
            )

    def test_catalog_delete_protected(self):
        CoinPackItem.objects.create(pack_variant=self.pv, issue=self.issue)
        with self.assertRaises(ProtectedError):
            self.issue.delete()

    def test_duplicate_issue_without_mint_rejected(self):
        with self.assertRaises(ValidationError):
            CoinIssue.objects.create(
                coin_type=self.coin, year=1373, calendar=Calendar.SOLAR_HIJRI
            )

    def test_unsaved_pack_parent_inline_checks_year(self):
        parent = CoinPackVariant(pack=self.pack, variant=self.variant)
        wrong = CoinIssue.objects.create(
            coin_type=self.coin, year=1374, calendar=Calendar.SOLAR_HIJRI
        )
        item = CoinPackItem(pack_variant=parent, issue=wrong)
        with self.assertRaises(ValidationError):
            item.clean()

    def test_currency_can_be_registered_without_known_issuer(self):
        currency = CoinCurrency.objects.create(name="ریال", slug="rial")
        self.coin.currency = currency
        self.coin.save()
        self.assertEqual(currency.issuers.count(), 0)

    def test_parent_period_issuer_change_rejected(self):
        self.period.issuer = self.other
        with self.assertRaises(ValidationError):
            self.period.save()
