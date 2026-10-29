"""Explicit public field lists: never expose purchase costs or storage locations."""

from django.db.models import Q
from rest_framework import serializers
from coins import models as m


class NamedSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    name_en = serializers.CharField()
    slug = serializers.CharField()


class ReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.CoinCatalogReference
        fields = ("catalog", "number", "url")


class CompositionSerializer(serializers.ModelSerializer):
    material = NamedSerializer()
    part_label = serializers.CharField(source="get_part_display")

    class Meta:
        model = m.CoinCompositionPart
        fields = ("part", "part_label", "position", "material", "fineness", "notes")


class ImageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    url = serializers.SerializerMethodField()
    alt_text = serializers.CharField(allow_null=True)
    is_main = serializers.BooleanField()
    view_type = serializers.SerializerMethodField()
    pack_item_id = serializers.SerializerMethodField()
    caption = serializers.SerializerMethodField()

    def get_url(self, obj):
        value = obj.image.url if obj.image else obj.source_url
        request = self.context.get("request")
        return request.build_absolute_uri(value) if value and request else value

    def get_view_type(self, obj):
        detail = getattr(obj, "coin_detail", None)
        return detail.view_type if detail else None

    def get_pack_item_id(self, obj):
        detail = getattr(obj, "coin_detail", None)
        return detail.pack_item_id if detail else None

    def get_caption(self, obj):
        detail = getattr(obj, "coin_detail", None)
        return detail.caption if detail else ""


class CatalogImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    alt_text = serializers.CharField(source="caption")
    is_main = serializers.SerializerMethodField()
    pack_item_id = serializers.SerializerMethodField()

    def get_url(self, obj):
        value = obj.image.url if obj.image else obj.source_url
        request = self.context.get("request")
        return request.build_absolute_uri(value) if value and request else value

    def get_is_main(self, obj):
        return obj.position == 0

    def get_pack_item_id(self, obj):
        return None

    class Meta:
        model = m.CoinCatalogImage
        fields = (
            "id",
            "url",
            "alt_text",
            "is_main",
            "pack_item_id",
            "view_type",
            "caption",
            "credit",
        )


class SaleSerializer(serializers.Serializer):
    """Shared shape for loose specimens and prepared pack variants."""

    id = serializers.IntegerField()
    variant_id = serializers.IntegerField()
    product_id = serializers.IntegerField(source="variant.product_id")
    product_slug = serializers.CharField(source="variant.product.slug")
    sku = serializers.CharField(source="variant.sku")
    variant_label = serializers.SerializerMethodField()
    price = serializers.DecimalField(
        source="variant.price", max_digits=12, decimal_places=0
    )
    discount_price = serializers.DecimalField(
        source="variant.discount_price",
        max_digits=12,
        decimal_places=0,
        allow_null=True,
    )
    effective_price = serializers.DecimalField(max_digits=12, decimal_places=0)
    available_stock = serializers.IntegerField()
    can_purchase = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    sale_mode = serializers.CharField()
    condition_notes = serializers.CharField()
    images = ImageSerializer(source="variant.images", many=True)

    def get_variant_label(self, obj):
        values = obj.variant.attributes.select_related("attribute").all()
        attributes = " / ".join(f"{value.attribute.name}: {value.value}" for value in values)
        return f"{obj.variant.product.name} · {attributes}" if attributes else obj.variant.product.name

    def get_can_purchase(self, obj):
        return obj.available_stock > 0 and obj.effective_price > 0

    def get_currency(self, obj):
        return "IRT"


class SpecimenSerializer(SaleSerializer):
    condition_grade = serializers.CharField()
    condition_label = serializers.CharField(source="get_condition_grade_display")
    cleaned = serializers.BooleanField(allow_null=True)
    scratched = serializers.BooleanField(allow_null=True)
    corroded = serializers.BooleanField(allow_null=True)
    edge_damaged = serializers.BooleanField(allow_null=True)
    holed = serializers.BooleanField(allow_null=True)
    bent = serializers.BooleanField(allow_null=True)
    repaired = serializers.BooleanField(allow_null=True)
    defect_notes = serializers.CharField()
    patina_description = serializers.CharField()
    mint_error_description = serializers.CharField()
    authenticity_notes = serializers.CharField()
    grading_company = serializers.CharField()
    certification_number = serializers.CharField()
    certification_url = serializers.CharField()
    grading_designation = serializers.CharField()
    numeric_grade = serializers.IntegerField(allow_null=True)
    measured_weight_g = serializers.DecimalField(
        max_digits=10, decimal_places=4, allow_null=True
    )
    measured_diameter_mm = serializers.DecimalField(
        max_digits=10, decimal_places=4, allow_null=True
    )
    measured_thickness_mm = serializers.DecimalField(
        max_digits=10, decimal_places=4, allow_null=True
    )
    packaging = serializers.CharField()


class IssueSerializer(serializers.ModelSerializer):
    images = CatalogImageSerializer(source="catalog_images", many=True)
    mint = NamedSerializer(allow_null=True)
    finish_label = serializers.CharField(source="get_finish_display")
    date_status_label = serializers.CharField(source="get_date_status_display")
    references = ReferenceSerializer(many=True)
    specimens = SpecimenSerializer(source="public_specimens", many=True)

    class Meta:
        model = m.CoinIssue
        fields = (
            "id",
            "year",
            "calendar",
            "date_status",
            "date_status_label",
            "date_inscription",
            "gregorian_year_start",
            "gregorian_year_end",
            "mint",
            "mint_mark",
            "variety_code",
            "variety_description",
            "description",
            "images",
            "finish",
            "finish_label",
            "mintage",
            "references",
            "specimens",
        )


class CoinCardSerializer(serializers.ModelSerializer):
    issuer = NamedSerializer()
    period = NamedSerializer(allow_null=True)
    min_price = serializers.DecimalField(
        max_digits=12, decimal_places=0, allow_null=True
    )
    in_stock = serializers.BooleanField()
    currency = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = m.CoinType
        fields = (
            "id",
            "name",
            "mint_year",
            "slug",
            "issuer",
            "period",
            "denomination_label",
            "introduction",
            "calendar",
            "year_start",
            "year_end",
            "construction",
            "shape",
            "min_price",
            "currency",
            "in_stock",
            "image",
        )

    def get_currency(self, obj):
        return "IRT"

    def get_image(self, obj):
        image = obj.card_image
        if image:
            return ImageSerializer(image, context=self.context).data
        reference = next(iter(obj.catalog_images.all()), None)
        return CatalogImageSerializer(reference, context=self.context).data if reference else None


class CoinDetailSerializer(serializers.ModelSerializer):
    related_years = serializers.SerializerMethodField()

    def get_related_years(self, obj):
        from .views import sales
        public_ids = sales(m.CoinSpecimen.objects.all()).values("issue__coin_type_id")
        rows = m.CoinType.objects.filter(
            name=obj.name, issuer_id=obj.issuer_id, calendar=obj.calendar,
            currency_id=obj.currency_id, face_value=obj.face_value,
            denomination_label=obj.denomination_label, mint_year__isnull=False,
            period_id=obj.period_id, ruler_id=obj.ruler_id, series_name=obj.series_name,
            construction=obj.construction, shape=obj.shape,
        ).filter(Q(is_published=True) | Q(pk__in=public_ids)).order_by("mint_year", "pk")
        return [{"slug": row.slug, "year": row.mint_year} for row in rows]

    images = CatalogImageSerializer(source="catalog_images", many=True)
    issuer = NamedSerializer()
    period = NamedSerializer(allow_null=True)
    ruler = NamedSerializer(allow_null=True)
    currency = NamedSerializer(allow_null=True)
    themes = NamedSerializer(many=True)
    composition_parts = CompositionSerializer(many=True)
    references = ReferenceSerializer(many=True)
    issues = IssueSerializer(many=True)
    shape_label = serializers.CharField(source="get_shape_display")
    construction_label = serializers.CharField(source="get_construction_display")
    edge_label = serializers.CharField(source="get_edge_type_display")

    class Meta:
        model = m.CoinType
        fields = (
            "id",
            "name",
            "mint_year",
            "related_years",
            "slug",
            "issuer",
            "period",
            "ruler",
            "currency",
            "face_value",
            "denomination_label",
            "issue_kind",
            "calendar",
            "calendar_notes",
            "year_start",
            "year_end",
            "construction",
            "construction_label",
            "shape",
            "shape_label",
            "shape_notes",
            "side_count",
            "has_hole",
            "weight_g",
            "diameter_mm",
            "width_mm",
            "height_mm",
            "thickness_mm",
            "edge_type",
            "edge_label",
            "edge_inscription",
            "edge_notes",
            "alignment_degrees",
            "obverse_description",
            "obverse_inscription",
            "obverse_designer",
            "reverse_description",
            "reverse_inscription",
            "reverse_designer",
            "languages",
            "themes",
            "series_name",
            "introduction",
            "story",
            "story_sources",
            "images",
            "description",
            "composition_parts",
            "references",
            "issues",
        )


class PackItemSerializer(serializers.ModelSerializer):
    coin_type_id = serializers.IntegerField(source="issue.coin_type_id")
    coin_slug = serializers.CharField(source="issue.coin_type.slug")
    coin_name = serializers.CharField(source="issue.coin_type.name")
    year = serializers.IntegerField(source="issue.year", allow_null=True)
    calendar = serializers.CharField(source="issue.calendar")
    finish = serializers.CharField(source="issue.finish")
    mint_mark = serializers.CharField(source="issue.mint_mark")
    condition_label = serializers.CharField(source="get_condition_grade_display")

    class Meta:
        model = m.CoinPackItem
        fields = (
            "id",
            "issue_id",
            "coin_type_id",
            "coin_slug",
            "coin_name",
            "year",
            "calendar",
            "finish",
            "mint_mark",
            "quantity",
            "condition_grade",
            "condition_label",
            "notes",
            "position",
        )


class PackVariantSerializer(SaleSerializer):
    packaging_notes = serializers.CharField()
    coin_count = serializers.SerializerMethodField()
    items = PackItemSerializer(many=True)

    def get_coin_count(self, obj):
        return sum(item.quantity for item in obj.items.all())


class PackCardSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name")
    slug = serializers.CharField(source="product.slug")
    issuer = NamedSerializer(allow_null=True)
    min_price = serializers.DecimalField(
        max_digits=12, decimal_places=0, allow_null=True
    )
    in_stock = serializers.BooleanField()
    currency = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = m.CoinPack
        fields = (
            "id",
            "name",
            "slug",
            "year",
            "calendar",
            "issuer",
            "is_complete",
            "min_price",
            "currency",
            "in_stock",
            "image",
        )

    get_currency = CoinCardSerializer.get_currency
    get_image = CoinCardSerializer.get_image


class PackDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name")
    slug = serializers.CharField(source="product.slug")
    issuer = NamedSerializer(allow_null=True)
    variants = PackVariantSerializer(source="public_variants", many=True)

    class Meta:
        model = m.CoinPack
        fields = (
            "id",
            "name",
            "slug",
            "year",
            "calendar",
            "calendar_notes",
            "issuer",
            "is_complete",
            "completeness_scope",
            "packaging",
            "description",
            "variants",
        )
