"""Staff-only lookups and zero-stock variant creation from a coin form."""

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from products.models import Product, ProductVariant
from . import models as m
from .variant_forms import QuickVariantForm


def check_access(request, create=False):
    model = {"specimen": m.CoinSpecimen, "pack-variant": m.CoinPackVariant}.get(
        request.GET.get("kind")
    )
    if model is None:
        raise PermissionDenied
    name = model._meta.model_name
    if not any(
        request.user.has_perm(f"coins.{action}_{name}") for action in ("add", "change")
    ):
        raise PermissionDenied
    if not request.user.has_perm("products.view_productvariant"):
        raise PermissionDenied
    if create and not request.user.has_perm("products.add_productvariant"):
        raise PermissionDenied


def variant_label(obj):
    return f"{obj.product.name} · {obj.sku}"


@staff_member_required(login_url="admin:login")
@require_GET
def lookup(request):
    check_access(request)
    q = request.GET.get("q", "").strip()[:120]
    try:
        page = int(request.GET.get("page", 1))
        if not 1 <= page <= 10000:
            raise ValueError
    except ValueError:
        return JsonResponse({"error": "صفحه معتبر نیست."}, status=400)
    if request.GET.get("target") == "product":
        if not request.user.has_perm("products.view_product"):
            raise PermissionDenied
        qs = Product.objects.all()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q))
        qs = qs.order_by("name", "pk")
        label = lambda obj: obj.name
    else:
        # Already linked variants cannot represent a second specimen/pack.
        qs = (
            ProductVariant.objects.select_related("product")
            .exclude(pk__in=m.CoinSpecimen.objects.values("variant_id"))
            .exclude(pk__in=m.CoinPackVariant.objects.values("variant_id"))
        )
        if q:
            qs = qs.filter(
                Q(sku__icontains=q)
                | Q(product__name__icontains=q)
                | Q(attributes__value__icontains=q)
            ).distinct()
        qs = qs.order_by("product__name", "sku", "pk")
        label = variant_label
    start = (page - 1) * 20
    rows = list(qs[start : start + 21])
    return JsonResponse(
        {
            "results": [{"id": obj.pk, "label": label(obj)} for obj in rows[:20]],
            "has_more": len(rows) > 20,
        }
    )


@staff_member_required(login_url="admin:login")
@require_POST
@csrf_protect
def create(request):
    check_access(request, create=True)
    if not request.user.has_perm("products.view_product"):
        raise PermissionDenied
    form = QuickVariantForm(request.POST)
    if form.is_valid():
        try:
            with transaction.atomic():
                variant = form.save(commit=False)
                variant.stock = (
                    0  # Stock must enter through the existing inventory flow.
                )
                variant.save()
        except IntegrityError:
            return JsonResponse(
                {"errors": {"sku": ["کد کالا تکراری است؛ کد دیگری وارد کنید."]}},
                status=400,
            )
        except ValidationError as error:
            return JsonResponse({"errors": {"__all__": error.messages}}, status=400)
        return JsonResponse(
            {"id": variant.pk, "label": variant_label(variant)}, status=201
        )
    return JsonResponse(
        {"errors": {key: list(values) for key, values in form.errors.items()}},
        status=400,
    )
