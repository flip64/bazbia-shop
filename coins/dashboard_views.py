"""Private catalog workspace. Public storefront continues to use sale listings."""

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction, models as db_models
from django.db.models import Q, Count, Prefetch, Exists, OuterRef, Min, Max
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from . import models as m
from products.models import ProductVariantImage

NS = "dashboard:coin_catalog:"
# Fixed allowlist: a URL can never select an unrelated application/model.
MODELS = {
    "type": m.CoinType,
    "issue": m.CoinIssue,
    "image": m.CoinCatalogImage,
    "composition": m.CoinCompositionPart,
    "reference": m.CoinCatalogReference,
    "specimen": m.CoinSpecimen,
    "issuer": m.CoinIssuer,
    "period": m.HistoricalPeriod,
    "ruler": m.CoinRuler,
    "currency": m.CoinCurrency,
    "material": m.CoinMaterial,
    "mint": m.CoinMint,
    "theme": m.CoinTheme,
    "pack": m.CoinPack,
    "pack-variant": m.CoinPackVariant,
    "pack-item": m.CoinPackItem,
    "sale-image": m.CoinImageDetail,
    "variant-image": ProductVariantImage,
}


def allowed(user, model, action):
    return user.has_perm(f"{model._meta.app_label}.{action}_{model._meta.model_name}")


def check(user, model, action):
    if not allowed(user, model, action):
        raise PermissionDenied


def context(request, **values):
    values["sections"] = [
        {
            "key": key,
            "label": (
                "بارگذاری عکس واریانت سکه"
                if key == "variant-image"
                else model._meta.verbose_name_plural
            ),
        }
        for key, model in MODELS.items()
        if key != "specimen" and allowed(request.user, model, "view")
    ]
    return values


def model_for(kind):
    if kind not in MODELS:
        raise Http404
    return MODELS[kind]


def object_coin(obj):
    if isinstance(obj, m.CoinType):
        return obj
    if hasattr(obj, "coin_type_id") and obj.coin_type_id:
        return obj.coin_type
    if hasattr(obj, "issue_id") and obj.issue_id:
        return obj.issue.coin_type
    if isinstance(obj, ProductVariantImage):
        specimen = (
            m.CoinSpecimen.objects.select_related("issue__coin_type")
            .filter(variant_id=obj.variant_id)
            .first()
        )
        return specimen.issue.coin_type if specimen else None
    return None


class CatalogFilters(forms.Form):
    q = forms.CharField(label="جستجو", required=False, max_length=120)
    issuer = forms.ModelChoiceField(
        label="کشور یا قلمرو",
        queryset=m.CoinIssuer.objects.all(),
        to_field_name="slug",
        required=False,
        empty_label="همه کشورها",
    )
    period = forms.ModelChoiceField(
        label="دوره تاریخی",
        queryset=m.HistoricalPeriod.objects.all(),
        to_field_name="slug",
        required=False,
        empty_label="همه دوره‌ها",
    )
    currency = forms.ModelChoiceField(
        label="واحد پول",
        queryset=m.CoinCurrency.objects.all(),
        to_field_name="slug",
        required=False,
        empty_label="همه واحدها",
    )
    material = forms.ModelChoiceField(
        label="جنس",
        queryset=m.CoinMaterial.objects.all(),
        to_field_name="slug",
        required=False,
        empty_label="همه جنس‌ها",
    )
    kind = forms.ChoiceField(
        label="نوع انتشار",
        choices=[("", "همه انواع"), *m.CoinType.Kind.choices],
        required=False,
    )
    shape = forms.ChoiceField(
        label="شکل",
        choices=[("", "همه شکل‌ها"), *m.CoinType.Shape.choices],
        required=False,
    )
    calendar = forms.ChoiceField(
        label="تقویم سال ضرب",
        choices=[("", "انتخاب تقویم"), *m.Calendar.choices],
        required=False,
    )
    year = forms.IntegerField(
        label="سال دقیق ضرب", required=False, min_value=-100000, max_value=100000
    )
    ordering = forms.ChoiceField(
        label="مرتب‌سازی",
        choices=[("", "کشور و نام"), ("newest", "تازه ثبت‌شده"), ("year", "سال ضرب")],
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data.get("issuer"):
            self.fields["period"].queryset = m.HistoricalPeriod.objects.filter(
                issuer__slug=self.data["issuer"]
            )
        self.fields["q"].widget.attrs.update(
            {"placeholder": "نام سکه، نوشته یا شماره کاتالوگ"}
        )
        self.fields["year"].widget.attrs["placeholder"] = "مثلاً ۱۳۷۳"

    def clean(self):
        values = super().clean()
        if values.get("year") is not None and not values.get("calendar"):
            self.add_error("calendar", "برای فیلتر سال، تقویم را انتخاب کنید.")
        return values


def reference_pair(images):
    """Never combine obverse and reverse belonging to different issues."""
    groups = {}
    for img in images:
        groups.setdefault(img.issue_id, []).append(img)
    chosen = groups.get(None)
    if chosen is None:
        chosen = next(iter(groups.values()), [])
    return {
        side: next((img for img in chosen if img.view_type == side), None)
        for side in ("obverse", "reverse")
    }


def parse_story(text):
    blocks = []
    for paragraph in text.replace("\r\n", "\n").split("\n\n"):
        text = paragraph.strip()
        if not text:
            continue
        if text.startswith("## "):
            blocks.append({"kind": "heading", "text": text[3:]})
        elif all(line.startswith("- ") for line in text.splitlines()):
            blocks.append(
                {"kind": "list", "lines": [line[2:] for line in text.splitlines()]}
            )
        else:
            blocks.append({"kind": "paragraph", "text": text})
    return blocks


@staff_member_required(login_url="admin:login")
@require_http_methods(["GET"])
def catalog_list(request):
    check(request.user, m.CoinType, "view")
    form = CatalogFilters(request.GET)
    qs = m.CoinType.objects.select_related("issuer", "period", "currency").annotate(
        issue_count=Count("issues", distinct=True),
        specimen_count=Count("issues__specimens", distinct=True),
        first_year=Min("issues__year"),
        last_year=Max("issues__year"),
    )
    selected_issuer = None
    selected_period = None
    if form.is_valid():
        data = form.cleaned_data
        for field in ("issuer", "period", "currency"):
            if data.get(field):
                qs = qs.filter(**{field: data[field]})
        selected_issuer, selected_period = data.get("issuer"), data.get("period")
        if data.get("material"):
            qs = qs.filter(composition_parts__material=data["material"])
        for field, lookup in (("kind", "issue_kind"), ("shape", "shape")):
            if data.get(field):
                qs = qs.filter(**{lookup: data[field]})
        if data.get("year") is not None:
            qs = qs.filter(
                Exists(
                    m.CoinIssue.objects.filter(
                        coin_type_id=OuterRef("pk"),
                        year=data["year"],
                        calendar=data["calendar"],
                    )
                )
            )
        elif data.get("calendar"):
            qs = qs.filter(calendar=data["calendar"])
        q = data.get("q")
        if q:
            text = (
                Q(name__icontains=q)
                | Q(slug__icontains=q)
                | Q(issuer__name__icontains=q)
                | Q(denomination_label__icontains=q)
                | Q(obverse_inscription__icontains=q)
                | Q(reverse_inscription__icontains=q)
            )
            if allowed(request.user, m.CoinCatalogReference, "view"):
                text |= Q(references__number__icontains=q)
            qs = qs.filter(text)
        ordering = {
            "newest": ("-created_at",),
            "year": ("calendar", "first_year", "name"),
        }.get(data.get("ordering"), ("issuer__name", "name"))
        qs = qs.order_by(*ordering, "pk").distinct()
    else:
        qs = qs.none()
    can_images = allowed(request.user, m.CoinCatalogImage, "view")
    if can_images:
        qs = qs.prefetch_related(
            Prefetch(
                "catalog_images",
                queryset=m.CoinCatalogImage.objects.select_related("issue"),
            )
        )
    if allowed(request.user, m.CoinCompositionPart, "view"):
        qs = qs.prefetch_related("composition_parts__material")
    if allowed(request.user, m.CoinCatalogReference, "view"):
        qs = qs.prefetch_related("references")
    page = Paginator(qs, 24).get_page(request.GET.get("page"))
    tiles = []
    for coin in page:
        tiles.append(
            {
                "coin": coin,
                "pair": reference_pair(
                    list(coin.catalog_images.all()) if can_images else []
                ),
                "materials": (
                    list(coin.composition_parts.all())
                    if allowed(request.user, m.CoinCompositionPart, "view")
                    else []
                ),
                "references": (
                    list(coin.references.all())
                    if allowed(request.user, m.CoinCatalogReference, "view")
                    else []
                ),
            }
        )
    countries = m.CoinIssuer.objects.annotate(coin_count=Count("coin_types")).filter(
        coin_count__gt=0
    )
    periods = (
        m.HistoricalPeriod.objects.filter(issuer=selected_issuer).annotate(
            coin_count=Count("coin_types")
        )
        if selected_issuer
        else []
    )
    return render(
        request,
        "coins/dashboard/list.html",
        context(
            request,
            page=page,
            tiles=tiles,
            filters=form,
            q=request.GET.get("q", ""),
            selected_issuer=selected_issuer,
            selected_period=selected_period,
            countries=countries,
            periods=periods,
            display="grid" if request.GET.get("view") == "grid" else "rows",
            can_add=allowed(request.user, m.CoinType, "add"),
        ),
    )


@staff_member_required(login_url="admin:login")
@require_http_methods(["GET"])
def country_browser(request):
    check(request.user, m.CoinType, "view")
    q = request.GET.get("q", "").strip()[:120]
    countries = m.CoinIssuer.objects.annotate(
        coin_count=Count("coin_types", distinct=True),
        period_count=Count("periods", distinct=True),
    )
    if q:
        countries = countries.filter(Q(name__icontains=q) | Q(name_en__icontains=q))
    return render(
        request,
        "coins/dashboard/countries.html",
        context(request, countries=countries, q=q),
    )


@staff_member_required(login_url="admin:login")
@require_http_methods(["GET"])
def catalog_detail(request, pk):
    check(request.user, m.CoinType, "view")
    coin = get_object_or_404(
        m.CoinType.objects.select_related(
            "issuer", "period", "ruler", "currency"
        ).prefetch_related("themes"),
        pk=pk,
    )
    rows = []
    for field in coin._meta.fields:
        value = getattr(coin, field.name)
        if field.choices:
            value = getattr(coin, f"get_{field.name}_display")()
        if isinstance(value, bool):
            value = "بله" if value else "خیر"
        label = (
            "آماده بودن اطلاعات (داخلی)"
            if field.name == "is_published" and isinstance(coin, m.CoinType)
            else field.verbose_name
        )
        rows.append((label, value))
    rows.append(("موضوع‌ها", "، ".join(t.name for t in coin.themes.all())))
    field_rows = dict(
        (field.name, rows[index]) for index, field in enumerate(coin._meta.fields)
    )
    groups = []
    missing_fields = []
    for title, names in [
        (
            "هویت و تاریخ",
            [
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
                "series_name",
                "languages",
            ],
        ),
        (
            "جنس و مشخصات فنی",
            [
                "construction",
                "shape",
                "shape_notes",
                "side_count",
                "has_hole",
                "weight_g",
                "diameter_mm",
                "width_mm",
                "height_mm",
                "thickness_mm",
                "edge_type",
                "edge_inscription",
                "edge_notes",
                "alignment_degrees",
            ],
        ),
        (
            "نقش و نوشتهٔ رو",
            ["obverse_description", "obverse_inscription", "obverse_designer"],
        ),
        (
            "نقش و نوشتهٔ پشت",
            ["reverse_description", "reverse_inscription", "reverse_designer"],
        ),
    ]:
        visible = []
        for name in names:
            value = getattr(coin, name)
            if value is None or value in ("", "unknown"):
                missing_fields.append(field_rows[name][0])
            else:
                visible.append(field_rows[name])
        groups.append({"title": title, "rows": visible})
    technical_names = ["id", "created_at", "updated_at", "slug", "is_published"]
    extra_rows = [field_rows[name] for name in technical_names]
    images = (
        list(coin.catalog_images.select_related("issue"))
        if allowed(request.user, m.CoinCatalogImage, "view")
        else []
    )
    issues = (
        list(
            coin.issues.select_related("mint")
            .annotate(sale_count=Count("specimens", distinct=True))
            .order_by("calendar", "year", "pk")
        )
        if allowed(request.user, m.CoinIssue, "view")
        else []
    )
    relations = []
    for key, title, qs in [
        (
            "composition",
            "ترکیب‌های فلزی",
            coin.composition_parts.select_related("material").all(),
        ),
        ("reference", "مراجع کاتالوگی نوع سکه", coin.references.all()),
        (
            "specimen",
            "نمونه‌های فروش",
            m.CoinSpecimen.objects.filter(issue__coin_type=coin).select_related(
                "issue", "variant__product"
            ),
        ),
    ]:
        model = MODELS[key]
        if allowed(request.user, model, "view"):
            relations.append(
                {
                    "key": key,
                    "title": title,
                    "objects": list(qs),
                    "can_add": allowed(request.user, model, "add"),
                    "can_edit": allowed(request.user, model, "change"),
                }
            )
    return render(
        request,
        "coins/dashboard/detail.html",
        context(
            request,
            coin=coin,
            rows=rows,
            groups=groups,
            extra_rows=extra_rows,
            missing_fields=missing_fields,
            images=images,
            pair=reference_pair(images),
            story_blocks=parse_story(coin.story or coin.description),
            issues=issues,
            can_add_issue=allowed(request.user, m.CoinIssue, "add"),
            can_edit_issue=allowed(request.user, m.CoinIssue, "change"),
            can_view_issue=allowed(request.user, m.CoinIssue, "view"),
            can_add_image=allowed(request.user, m.CoinCatalogImage, "add"),
            can_edit_image=allowed(request.user, m.CoinCatalogImage, "change"),
            relations=relations,
            can_edit=allowed(request.user, m.CoinType, "change"),
        ),
    )


@staff_member_required(login_url="admin:login")
@require_http_methods(["GET"])
def record_list(request, kind):
    model = model_for(kind)
    check(request.user, model, "view")
    qs = model.objects.all().order_by("-pk")
    q = request.GET.get("q", "").strip()[:120]
    # Only concrete text fields are searched; private notes are staff-only.
    if q:
        query = Q()
        for field in model._meta.fields:
            if isinstance(field, (db_models.CharField, db_models.TextField)):
                query |= Q(**{field.name + "__icontains": q})
        qs = qs.filter(query) if query else qs.none()
    return render(
        request,
        "coins/dashboard/records.html",
        context(
            request,
            kind=kind,
            title=(
                "عکس‌های واریانت سکه"
                if model is ProductVariantImage
                else model._meta.verbose_name_plural
            ),
            page=Paginator(qs, 30).get_page(request.GET.get("page")),
            q=q,
            can_add=allowed(request.user, model, "add"),
            can_edit=allowed(request.user, model, "change"),
        ),
    )


@staff_member_required(login_url="admin:login")
@require_http_methods(["GET", "POST"])
@csrf_protect
def record_edit(request, kind, pk=None):
    model = model_for(kind)
    check(request.user, model, "change" if pk else "add")
    obj = get_object_or_404(model, pk=pk) if pk else None
    if model is ProductVariantImage:
        check(request.user, m.CoinImageDetail, "change" if pk else "add")
        from .variant_forms import CoinVariantImageForm

        Form = CoinVariantImageForm
    else:
        Form = forms.modelform_factory(model, fields="__all__")
    initial = {}
    coin_id = request.GET.get("coin")
    if not obj and model is m.CoinType and request.GET.get("issuer"):
        issuer = m.CoinIssuer.objects.filter(slug=request.GET["issuer"]).first()
        if issuer:
            initial["issuer"] = issuer.pk
    if not obj and coin_id and coin_id.isdecimal():
        coin = get_object_or_404(m.CoinType, pk=int(coin_id))
        if "coin_type" in Form.base_fields:
            initial["coin_type"] = coin.pk
        if model is m.CoinIssue:
            initial["calendar"] = coin.calendar
            initial["year"] = coin.mint_year
        if "issue" in Form.base_fields and request.GET.get("issue", "").isdecimal():
            issue = get_object_or_404(
                m.CoinIssue, pk=int(request.GET["issue"]), coin_type=coin
            )
            initial["issue"] = issue.pk
    form = Form(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=obj,
        initial=initial,
    )
    variant_picker = model in (m.CoinSpecimen, m.CoinPackVariant, ProductVariantImage)
    if variant_picker:
        from products.models import ProductVariant

        selected = (
            request.POST.get("variant")
            if request.method == "POST"
            else getattr(obj, "variant_id", None) or request.GET.get("variant")
        )
        selected = str(selected or "")
        if not form.is_bound and not obj and selected.isdecimal():
            form.initial["variant"] = int(selected)
        form.fields["variant"].queryset = (
            ProductVariant.objects.filter(pk=int(selected)).select_related("product")
            if selected.isdecimal()
            else ProductVariant.objects.none()
        )
        form.fields["variant"].label_from_instance = (
            lambda value: f"{value.product.name} · {value.sku}"
        )
    if not obj and coin_id and coin_id.isdecimal():
        if "issue" in form.fields:
            form.fields["issue"].queryset = m.CoinIssue.objects.filter(
                coin_type_id=int(coin_id)
            )
    if model is m.CoinType:
        form.fields["is_published"].label = "انتشار شناسنامه در کاتالوگ"
        form.fields["is_published"].help_text = (
            "شناسنامه بدون فروش نیز قابل نمایش است. اتصال به واریانت جداگانه مدیریت می‌شود."
        )
    for field in form.fields.values():
        if isinstance(field.widget, forms.Textarea):
            field.widget.attrs["rows"] = 5
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                obj = form.save()
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "اطلاعات ذخیره شد.")
            coin = object_coin(obj)
            if coin and allowed(request.user, m.CoinType, "view"):
                section = {
                    "issue": "years",
                    "image": "images",
                    "variant-image": "sales",
                    "composition": "specs",
                    "reference": "references",
                    "specimen": "sales",
                }.get(kind, "overview")
                return redirect(
                    reverse(NS + "detail", kwargs={"pk": coin.pk}) + "#" + section
                )
            if allowed(request.user, model, "view"):
                return redirect(NS + "record-detail", kind=kind, pk=obj.pk)
            if allowed(request.user, model, "change"):
                return redirect(NS + "edit", kind=kind, pk=obj.pk)
            return redirect(NS + "create", kind=kind)
    parent_coin = (
        object_coin(obj) if obj else (coin if coin_id and coin_id.isdecimal() else None)
    )
    groups = []
    remaining = list(form.fields)
    if model is m.CoinType:
        for title, names in [
            (
                "شناسه و دوره",
                [
                    "name",
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
                ],
            ),
            (
                "جنس، شکل و اندازه",
                [
                    "construction",
                    "shape",
                    "shape_notes",
                    "side_count",
                    "has_hole",
                    "weight_g",
                    "diameter_mm",
                    "width_mm",
                    "height_mm",
                    "thickness_mm",
                    "edge_type",
                    "edge_inscription",
                    "edge_notes",
                    "alignment_degrees",
                ],
            ),
            (
                "نقش‌ها و نوشته‌ها",
                [
                    "obverse_description",
                    "obverse_inscription",
                    "obverse_designer",
                    "reverse_description",
                    "reverse_inscription",
                    "reverse_designer",
                    "languages",
                    "themes",
                    "series_name",
                ],
            ),
            (
                "معرفی و داستان",
                [
                    "introduction",
                    "description",
                    "story",
                    "story_sources",
                    "is_published",
                ],
            ),
        ]:
            fields = [form[name] for name in names if name in remaining]
            remaining = [name for name in remaining if name not in names]
            groups.append({"title": title, "fields": fields})
    if remaining:
        groups.append(
            {"title": "اطلاعات", "fields": [form[name] for name in remaining]}
        )
    return render(
        request,
        "coins/dashboard/form.html",
        context(
            request,
            form=form,
            field_groups=groups,
            parent_coin=parent_coin,
            variant_picker=variant_picker,
            can_create_variant=(
                variant_picker
                and model is not ProductVariantImage
                and request.user.has_perm("products.add_productvariant")
                and request.user.has_perm("products.view_productvariant")
                and request.user.has_perm("products.view_product")
            ),
            kind=kind,
            obj=obj,
            title=(
                "عکس واریانت سکه"
                if model is ProductVariantImage
                else model._meta.verbose_name
            ),
        ),
    )


@staff_member_required(login_url="admin:login")
@require_http_methods(["GET"])
def record_detail(request, kind, pk):
    model = model_for(kind)
    check(request.user, model, "view")
    obj = get_object_or_404(model, pk=pk)
    rows = []
    for field in model._meta.fields:
        value = getattr(obj, field.name)
        if field.choices:
            value = getattr(obj, f"get_{field.name}_display")()
        if isinstance(value, bool):
            value = "بله" if value else "خیر"
        rows.append((field.verbose_name, value))
    for field in model._meta.many_to_many:
        rows.append(
            (
                field.verbose_name,
                "، ".join(str(v) for v in getattr(obj, field.name).all()),
            )
        )
    return render(
        request,
        "coins/dashboard/record_detail.html",
        context(
            request,
            obj=obj,
            kind=kind,
            rows=rows,
            title=(
                "عکس واریانت سکه"
                if model is ProductVariantImage
                else model._meta.verbose_name
            ),
            can_edit=allowed(request.user, model, "change"),
            product_id=(
                obj.variant.product_id
                if isinstance(obj, (m.CoinSpecimen, m.CoinPackVariant))
                else None
            ),
        ),
    )
