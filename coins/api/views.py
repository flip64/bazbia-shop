from decimal import Decimal

from django.db.models import (
    Case,
    When,
    F,
    Q,
    Exists,
    OuterRef,
    Subquery,
    Prefetch,
    BooleanField,
    Value,
)
from rest_framework import serializers, generics
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from coins import models as m
from products.models import ProductVariant, ProductVariantImage
from products.services.variant_stock import VariantStockService
from . import serializers as s


class QuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, max_length=120, allow_blank=True)
    issuer = serializers.SlugField(required=False, max_length=180)
    period = serializers.SlugField(required=False, max_length=180)
    ruler = serializers.SlugField(required=False, max_length=180)
    material = serializers.SlugField(required=False, max_length=180)
    currency = serializers.SlugField(required=False, max_length=180)
    theme = serializers.SlugField(required=False, max_length=180)
    mint = serializers.SlugField(required=False, max_length=180)
    shape = serializers.ChoiceField(choices=m.CoinType.Shape.choices, required=False)
    construction = serializers.ChoiceField(
        choices=m.CoinType.Construction.choices, required=False
    )
    issue_kind = serializers.ChoiceField(
        choices=m.CoinType.Kind.choices, required=False
    )
    calendar = serializers.ChoiceField(choices=m.Calendar.choices, required=False)
    year = serializers.IntegerField(required=False, min_value=-100000, max_value=100000)
    year_min = serializers.IntegerField(
        required=False, min_value=-100000, max_value=100000
    )
    year_max = serializers.IntegerField(
        required=False, min_value=-100000, max_value=100000
    )
    condition = serializers.ChoiceField(choices=m.Condition.choices, required=False)
    finish = serializers.ChoiceField(choices=m.Finish.choices, required=False)
    min_price = serializers.DecimalField(
        required=False, max_digits=12, decimal_places=0, min_value=Decimal("0")
    )
    max_price = serializers.DecimalField(
        required=False, max_digits=12, decimal_places=0, min_value=Decimal("0")
    )
    in_stock = serializers.BooleanField(required=False)
    is_complete = serializers.BooleanField(required=False)
    ordering = serializers.ChoiceField(
        choices=["price", "-price", "name", "-name", "newest"], required=False
    )
    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)

    def validate(self, values):
        if (
            any(k in values for k in ("year", "year_min", "year_max"))
            and "calendar" not in values
        ):
            raise serializers.ValidationError(
                {"calendar": "برای فیلتر سال، تقویم را مشخص کنید."}
            )
        if "year" in values and any(k in values for k in ("year_min", "year_max")):
            raise serializers.ValidationError(
                {"year": "سال دقیق و بازه سال را هم‌زمان نفرستید."}
            )
        for low, high in [("year_min", "year_max"), ("min_price", "max_price")]:
            if low in values and high in values and values[low] > values[high]:
                raise serializers.ValidationError(
                    {high: "انتهای بازه از ابتدا کمتر است."}
                )
        return values


def params(request, pack=False):
    allowed = set(QuerySerializer().fields)
    if not pack:
        allowed.remove("is_complete")
    unknown = set(request.query_params) - allowed
    if unknown:
        raise ValidationError({k: "پارامتر پشتیبانی نمی‌شود." for k in sorted(unknown)})
    repeated = [
        k for k in request.query_params if len(request.query_params.getlist(k)) > 1
    ]
    if repeated:
        raise ValidationError(
            {k: "هر فیلتر را فقط یک بار ارسال کنید." for k in repeated}
        )
    # Use a plain mapping: HTML QueryDict treats omitted booleans as False.
    query = QuerySerializer(data=request.query_params.dict())
    query.is_valid(raise_exception=True)
    return query.validated_data


class Pagination(PageNumberPagination):
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100


class PublicAPI:
    permission_classes = [AllowAny]
    authentication_classes = []


def sales(queryset):
    stock = VariantStockService.annotate(
        ProductVariant.objects.filter(pk=OuterRef("variant_id"))
    )
    return (
        queryset.filter(variant__product__is_active=True)
        .select_related("variant__product")
        .annotate(
            available_stock=Subquery(stock.values("available_stock")[:1]),
            effective_price=Case(
                When(
                    variant__discount_price__isnull=False,
                    then=F("variant__discount_price"),
                ),
                default=F("variant__price"),
            ),
        )
    )


def filter_sale(queryset, p):
    for name, lookup in [
        ("min_price", "effective_price__gte"),
        ("max_price", "effective_price__lte"),
    ]:
        if name in p:
            queryset = queryset.filter(**{lookup: p[name]})
    if "in_stock" in p:
        queryset = (
            queryset.filter(available_stock__gt=0)
            if p["in_stock"]
            else queryset.filter(available_stock__lte=0)
        )
    return queryset


def catalog_q(p, prefix=""):
    result = Q()
    mapping = {
        "issuer": "coin_type__issuer__slug",
        "period": "coin_type__period__slug",
        "ruler": "coin_type__ruler__slug",
        "currency": "coin_type__currency__slug",
        "material": "coin_type__composition_parts__material__slug",
        "theme": "coin_type__themes__slug",
        "shape": "coin_type__shape",
        "construction": "coin_type__construction",
        "issue_kind": "coin_type__issue_kind",
        "mint": "mint__slug",
        "finish": "finish",
        "calendar": "calendar",
        "year": "year",
        "year_min": "year__gte",
        "year_max": "year__lte",
    }
    for key, lookup in mapping.items():
        if key in p:
            result &= Q(**{prefix + lookup: p[key]})
    return result


def image_prefetch():
    return Prefetch(
        "variant__images",
        queryset=ProductVariantImage.objects.select_related("coin_detail").order_by(
            "-is_main", "coin_detail__position", "pk"
        ),
    )


def card_annotations(queryset, matched, name_field, p):
    cheapest = matched.annotate(
        sale_ready=Case(
            When(available_stock__gt=0, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )
    ).order_by("-sale_ready", "effective_price", "pk")
    queryset = queryset.annotate(
        min_price=Subquery(cheapest.values("effective_price")[:1]),
        first_variant_id=Subquery(cheapest.values("variant_id")[:1]),
        in_stock=Exists(matched.filter(available_stock__gt=0)),
    )
    ordering = p.get("ordering")
    fields = {
        "price": ["min_price"],
        "-price": ["-min_price"],
        "name": [name_field],
        "-name": ["-" + name_field],
        "newest": ["-created_at"],
    }.get(ordering, ["-in_stock", "min_price"])
    return queryset.order_by(*fields, "pk")


class CardList(PublicAPI, generics.ListAPIView):
    pagination_class = Pagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        rows = list(page if page is not None else queryset)
        ids = [row.first_variant_id for row in rows]
        images = (
            ProductVariantImage.objects.filter(variant_id__in=ids)
            .select_related("coin_detail")
            .order_by("-is_main", "coin_detail__position", "pk")
        )
        first = {}
        for image in images:
            first.setdefault(image.variant_id, image)
        for row in rows:
            row.card_image = first.get(row.first_variant_id)
        data = self.get_serializer(rows, many=True).data
        return self.get_paginated_response(data) if page is not None else Response(data)


class CoinListView(CardList):
    serializer_class = s.CoinCardSerializer

    def get_queryset(self):
        p = params(self.request)
        selected = filter_sale(sales(m.CoinSpecimen.objects.all()), p).filter(
            catalog_q(p, "issue__")
        )
        if "condition" in p:
            selected = selected.filter(condition_grade=p["condition"])
        if p.get("q"):
            text = p["q"]
            selected = selected.filter(
                Q(issue__coin_type__name__icontains=text)
                | Q(variant__product__name__icontains=text)
                | Q(issue__coin_type__obverse_inscription__icontains=text)
                | Q(issue__coin_type__reverse_inscription__icontains=text)
            )
        qs = m.CoinType.objects.filter(
            pk__in=selected.values("issue__coin_type_id")
        ).select_related("issuer", "period")
        correlated = selected.filter(issue__coin_type_id=OuterRef("pk"))
        return card_annotations(qs, correlated, "name", p)


class CoinDetailView(PublicAPI, generics.RetrieveAPIView):
    serializer_class = s.CoinDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        public = sales(m.CoinSpecimen.objects.all()).prefetch_related(image_prefetch())
        issues = (
            m.CoinIssue.objects.select_related("mint")
            .prefetch_related(
                "references",
                Prefetch("specimens", queryset=public, to_attr="public_specimens"),
            )
            .order_by("year", "pk")
        )
        return (
            m.CoinType.objects.filter(pk__in=public.values("issue__coin_type_id"))
            .select_related("issuer", "period", "ruler", "currency")
            .prefetch_related(
                "themes",
                "references",
                "composition_parts__material",
                Prefetch("issues", queryset=issues),
            )
        )


class PackListView(CardList):
    serializer_class = s.PackCardSerializer

    def get_queryset(self):
        p = params(self.request, pack=True)
        items_q = catalog_q(p, "issue__")
        if "condition" in p:
            items_q &= Q(condition_grade=p["condition"])
        items = m.CoinPackItem.objects.filter(pack_variant_id=OuterRef("pk")).filter(
            items_q
        )
        selected = filter_sale(sales(m.CoinPackVariant.objects.all()), p).filter(
            Exists(items)
        )
        qs = m.CoinPack.objects.filter(
            product__is_active=True, pk__in=selected.values("pack_id")
        ).select_related("product", "issuer")
        if "is_complete" in p:
            qs = qs.filter(is_complete=p["is_complete"])
        # A pack's year and issuer are metadata of the entire package.
        for key, lookup in [
            ("year", "year"),
            ("year_min", "year__gte"),
            ("year_max", "year__lte"),
            ("calendar", "calendar"),
            ("issuer", "issuer__slug"),
        ]:
            if key in p:
                qs = qs.filter(**{lookup: p[key]})
        if p.get("q"):
            qs = qs.filter(
                Q(product__name__icontains=p["q"]) | Q(description__icontains=p["q"])
            )
        return card_annotations(
            qs, selected.filter(pack_id=OuterRef("pk")), "product__name", p
        )


class PackDetailView(PublicAPI, generics.RetrieveAPIView):
    serializer_class = s.PackDetailSerializer
    lookup_field = "product__slug"
    lookup_url_kwarg = "slug"

    def get_queryset(self):
        items = m.CoinPackItem.objects.select_related("issue__coin_type")
        public = (
            sales(m.CoinPackVariant.objects.all())
            .filter(items__isnull=False)
            .distinct()
            .prefetch_related(image_prefetch(), Prefetch("items", queryset=items))
        )
        return (
            m.CoinPack.objects.filter(
                product__is_active=True, pk__in=public.values("pack_id")
            )
            .select_related("product", "issuer")
            .prefetch_related(
                Prefetch("pack_variants", queryset=public, to_attr="public_variants")
            )
        )


class FilterView(PublicAPI, APIView):
    def get(self, request):
        public_sales = sales(m.CoinSpecimen.objects.all())
        pack_items = m.CoinPackItem.objects.filter(
            pack_variant__variant__product__is_active=True
        )
        public_types = m.CoinType.objects.filter(
            Q(pk__in=public_sales.values("issue__coin_type_id"))
            | Q(pk__in=pack_items.values("issue__coin_type_id"))
        )

        def named(model, ids):
            return s.NamedSerializer(
                model.objects.filter(pk__in=ids).order_by("name", "pk"), many=True
            ).data

        def choices(values):
            return [{"value": value, "label": label} for value, label in values]

        issue_ids = m.CoinIssue.objects.filter(
            Q(pk__in=public_sales.values("issue_id"))
            | Q(pk__in=pack_items.values("issue_id"))
        ).values("pk")
        years = (
            m.CoinIssue.objects.filter(pk__in=issue_ids, year__isnull=False)
            .values("calendar", "year")
            .distinct()
            .order_by("calendar", "-year")
        )
        return Response(
            {
                "issuers": named(m.CoinIssuer, public_types.values("issuer_id")),
                "periods": named(m.HistoricalPeriod, public_types.values("period_id")),
                "rulers": named(m.CoinRuler, public_types.values("ruler_id")),
                "currencies": named(m.CoinCurrency, public_types.values("currency_id")),
                "materials": named(
                    m.CoinMaterial,
                    m.CoinCompositionPart.objects.filter(
                        coin_type__in=public_types
                    ).values("material_id"),
                ),
                "themes": named(m.CoinTheme, public_types.values("themes__id")),
                "mints": named(
                    m.CoinMint,
                    m.CoinIssue.objects.filter(pk__in=issue_ids).values("mint_id"),
                ),
                "years": list(years),
                "calendars": choices(m.Calendar.choices),
                "shapes": choices(m.CoinType.Shape.choices),
                "constructions": choices(m.CoinType.Construction.choices),
                "issue_kinds": choices(m.CoinType.Kind.choices),
                "conditions": choices(m.Condition.choices),
                "finishes": choices(m.Finish.choices),
                "ordering": [
                    {"value": "price", "label": "ارزان‌ترین"},
                    {"value": "-price", "label": "گران‌ترین"},
                    {"value": "name", "label": "نام"},
                    {"value": "-name", "label": "نام معکوس"},
                    {"value": "newest", "label": "جدیدترین"},
                ],
            }
        )
