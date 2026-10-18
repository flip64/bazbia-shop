"""Private catalog workspace. Public storefront continues to use sale listings."""

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction, models as db_models
from django.db.models import Q, Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from . import models as m

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
}


def allowed(user, model, action):
    return user.has_perm(f"coins.{action}_{model._meta.model_name}")


def check(user, model, action):
    if not allowed(user, model, action):
        raise PermissionDenied


def context(request, **values):
    values["sections"] = [
        {"key": key, "label": model._meta.verbose_name_plural}
        for key, model in MODELS.items()
        if allowed(request.user, model, "view")
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
    return None


@staff_member_required(login_url="admin:login")
@require_http_methods(["GET"])
def catalog_list(request):
    check(request.user, m.CoinType, "view")
    qs = m.CoinType.objects.select_related("issuer", "period").annotate(
        issue_count=Count("issues", distinct=True),
        specimen_count=Count("issues__specimens", distinct=True),
    )
    q = request.GET.get("q", "").strip()[:120]
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(slug__icontains=q) | Q(issuer__name__icontains=q)
        )
    page = Paginator(qs.order_by("name", "pk"), 30).get_page(request.GET.get("page"))
    return render(
        request,
        "coins/dashboard/list.html",
        context(
            request, page=page, q=q, can_add=allowed(request.user, m.CoinType, "add")
        ),
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
    relations = []
    for key, title, qs in [
        ("issue", "سال‌ها و گونه‌های ضرب", coin.issues.select_related("mint").all()),
        (
            "composition",
            "ترکیب‌های فلزی",
            coin.composition_parts.select_related("material").all(),
        ),
        ("reference", "مراجع کاتالوگی نوع سکه", coin.references.all()),
        ("image", "تصاویر مرجع", coin.catalog_images.all()),
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
            title=model._meta.verbose_name_plural,
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
    Form = forms.modelform_factory(model, fields="__all__")
    initial = {}
    coin_id = request.GET.get("coin")
    if not obj and coin_id and coin_id.isdecimal():
        coin = get_object_or_404(m.CoinType, pk=int(coin_id))
        if "coin_type" in Form.base_fields:
            initial["coin_type"] = coin.pk
        if model is m.CoinIssue:
            initial["calendar"] = coin.calendar
    form = Form(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=obj,
        initial=initial,
    )
    if not obj and coin_id and coin_id.isdecimal():
        if "issue" in form.fields:
            form.fields["issue"].queryset = m.CoinIssue.objects.filter(
                coin_type_id=int(coin_id)
            )
    if model is m.CoinType:
        form.fields["is_published"].label = "اطلاعات کاتالوگی آماده است (وضعیت داخلی)"
        form.fields["is_published"].help_text = (
            "نمایش در فروشگاه فقط با انتشار نمونه فروش انجام می‌شود."
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
                return redirect(NS + "detail", pk=coin.pk)
            if allowed(request.user, model, "view"):
                return redirect(NS + "record-detail", kind=kind, pk=obj.pk)
            if allowed(request.user, model, "change"):
                return redirect(NS + "edit", kind=kind, pk=obj.pk)
            return redirect(NS + "create", kind=kind)
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
            kind=kind,
            obj=obj,
            title=model._meta.verbose_name,
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
            title=model._meta.verbose_name,
            can_edit=allowed(request.user, model, "change"),
            product_id=(
                obj.variant.product_id
                if isinstance(obj, (m.CoinSpecimen, m.CoinPackVariant))
                else None
            ),
        ),
    )
