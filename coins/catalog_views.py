"""Catalog-only registration and explicit connections to existing stock variants."""
from uuid import uuid4
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from products.models import ProductVariant
from . import models as m
from .catalog_forms import CatalogCoinForm, VariantConnectionForm
from .dashboard_views import check, context
from .services import set_publication

NS = "dashboard:coin_catalog:"


@staff_member_required(login_url="admin:login")
@require_http_methods(["GET", "POST"])
@csrf_protect
def register_coin(request, pk=None):
    coin = get_object_or_404(m.CoinType, pk=pk) if pk else None
    check(request.user, m.CoinType, "change" if coin else "add")
    source = None
    initial = {}
    copy_id = request.GET.get("copy", "")
    if not coin and copy_id.isdecimal():
        check(request.user, m.CoinType, "view")
        source = get_object_or_404(m.CoinType, pk=copy_id)
        from django.forms.models import model_to_dict
        initial = model_to_dict(source, exclude=("id", "slug", "mint_year", "year_start", "year_end", "is_published"))
        initial["is_published"] = False
    form = CatalogCoinForm(request.POST if request.method == "POST" else None,
                           request.FILES if request.method == "POST" else None, instance=coin, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                obj = form.save(commit=False)
                creating = not obj.pk
                if not obj.pk:
                    obj.slug = "coin-" + uuid4().hex
                obj.save()
                form.save_m2m()
                if creating or not obj.issues.exists():
                    check(request.user, m.CoinIssue, "add")
                    m.CoinIssue.objects.create(coin_type=obj, year=obj.mint_year,
                        calendar=obj.calendar, date_status=m.CoinIssue.DateStatus.KNOWN)
                if source:
                    # Copy shared specifications only. Photos and sale links belong to the new year.
                    if source.composition_parts.exists():
                        check(request.user, m.CoinCompositionPart, "add")
                        for part in source.composition_parts.all():
                            part.pk = None
                            part.coin_type = obj
                            part.save()
                    if source.references.exists():
                        check(request.user, m.CoinCatalogReference, "add")
                        for reference in source.references.all():
                            reference.pk = None
                            reference.coin_type = obj
                            reference.save()
                for side in ("obverse", "reverse"):
                    if form.cleaned_data.get(side):
                        check(request.user, m.CoinCatalogImage, "add")
                        m.CoinCatalogImage.objects.create(coin_type=obj, image=form.cleaned_data[side], view_type=side)
            messages.success(request, "شناسنامه سکه ذخیره شد. اتصال به فروش از بخش جداگانه انجام می‌شود.")
            return redirect(NS + "detail", pk=obj.pk)
        except (ValidationError, IntegrityError) as exc:
            form.add_error(None, " / ".join(exc.messages) if isinstance(exc, ValidationError) else "اطلاعات تکراری یا ناسازگار است.")
    basic = {"mint_year", "name", "issuer", "denomination_label", "calendar", "introduction", "story", "obverse", "reverse", "is_published"}
    return render(request, "coins/dashboard/catalog_coin.html", context(request, coin=coin, source=source, form=form,
        basic_fields=[field for field in form if field.name in basic],
        advanced_fields=[field for field in form if field.name not in basic]))


@staff_member_required(login_url="admin:login")
@require_http_methods(["GET", "POST"])
@csrf_protect
def connections(request, pk):
    coin = get_object_or_404(m.CoinType, pk=pk)
    check(request.user, m.CoinType, "change")
    check(request.user, m.CoinSpecimen, "view")
    check(request.user, ProductVariant, "view")
    form = VariantConnectionForm(request.POST if request.method == "POST" else None,
        coin=coin, variant_id=request.POST.get("variant"))
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "disconnect":
                check(request.user, m.CoinSpecimen, "change")
                check(request.user, ProductVariant, "change")
                # Keep the internal relationship for snapshots, stock guards and reactivation.
                # Only its publication is removed; a persistent flag blocks every purchase path.
                with transaction.atomic():
                    link_id = request.POST.get("link", "")
                    if not link_id.isdecimal():
                        raise ValidationError("اتصال انتخاب‌شده معتبر نیست.")
                    link = get_object_or_404(m.CoinSpecimen, pk=link_id, issue__coin_type=coin)
                    variant = ProductVariant.objects.select_for_update().get(pk=link.variant_id)
                    link = m.CoinSpecimen.objects.select_for_update().get(pk=link.pk)
                    if link.is_published:
                        m.CoinType.objects.filter(pk=coin.pk).update(is_published=True)
                    set_publication(link, False)
                    variant.is_sellable = False
                    variant.save(update_fields=["is_sellable"])
                messages.success(request, "اتصال فروش قطع شد. واریانت غیرقابل‌فروش است؛ موجودی انبار حفظ شد.")
                return redirect(NS + "connections", pk=pk)
            elif action == "connect" and form.is_valid():
                check(request.user, m.CoinSpecimen, "add")
                check(request.user, ProductVariant, "change")
                with transaction.atomic():
                    variant = ProductVariant.objects.select_for_update().select_related("product").get(pk=form.cleaned_data["variant"].pk)
                    if not variant.product.is_active:
                        raise ValidationError("ابتدا محصول را در بخش محصولات فعال کنید.")
                    link = m.CoinSpecimen.objects.select_for_update().filter(variant=variant).first()
                    if link and link.issue.coin_type_id != coin.pk:
                        raise ValidationError("این واریانت به سکه دیگری متصل است؛ ابتدا اتصال قبلی را بررسی کنید.")
                    if link:
                        check(request.user, m.CoinSpecimen, "change")
                        if link.issue_id != form.cleaned_data["issue"].pk:
                            raise ValidationError("سال ضرب این اتصال با انتخاب جدید متفاوت است. برای حفظ سوابق، واریانت دیگری انتخاب کنید.")
                    else:
                        link = m.CoinSpecimen.objects.create(issue=form.cleaned_data["issue"], variant=variant,
                            sale_mode=m.SaleMode.SIMILAR, catalog_link=True)
                    variant.is_sellable = True
                    variant.save(update_fields=["is_sellable"])
                    set_publication(link, True)
                    m.CoinType.objects.filter(pk=coin.pk).update(is_published=True)
                messages.success(request, "واریانت به سکه متصل و فروش فعال شد.")
                return redirect(NS + "connections", pk=pk)
            elif action != "connect":
                form.add_error(None, "عملیات معتبر نیست.")
        except (ValidationError, IntegrityError) as exc:
            form.add_error(None, " / ".join(exc.messages) if isinstance(exc, ValidationError) else "این واریانت هم‌زمان تغییر کرده است؛ صفحه را تازه کنید.")
    links = m.CoinSpecimen.objects.filter(issue__coin_type=coin).select_related("issue", "variant__product")
    return render(request, "coins/dashboard/connections.html", context(request, coin=coin, form=form,
        links=links, kind="connection", variant_picker=True, can_create_variant=False))
