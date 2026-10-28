"""Unified registration and sale workspace; existing catalog data is preserved."""
from uuid import uuid4
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from products.models import Product, ProductVariant, ProductVariantImage
from inventory.models import InventoryLot, InventoryMovement
from . import models as m
from .dashboard_views import check, context
from .simple_forms import PackForm, PackItems
from .services import readiness_errors, set_publication
from .guards import inventory_write

NS = 'dashboard:coin_catalog:'


def upload(listing, file, side, item=None):
    if not file:
        return
    # Parent listing exists before image metadata is validated.
    image = ProductVariantImage.objects.create(variant=listing.variant, image=file,
        is_main=not listing.variant.images.exists(), alt_text=listing.variant.product.name)
    m.CoinImageDetail.objects.create(image=image, view_type=side, pack_item=item)


def enter_stock(user, listing, quantity, unit_cost):
    if not quantity:
        return
    check(user, InventoryLot, 'add')
    check(user, InventoryMovement, 'add')
    check(user, ProductVariant, 'change')
    with inventory_write([listing.variant_id], force=True):
        variant = ProductVariant.objects.select_for_update().get(pk=listing.variant_id)
        lots = InventoryLot.objects.filter(product_variant=variant).aggregate(n=Sum('quantity_remaining'))['n'] or 0
        if lots != variant.stock:
            raise ValidationError('موجودی قبلی با سوابق خرید هماهنگ نیست. ورود جدید ذخیره نشد؛ ابتدا سوابق قبلی را در انبار بررسی کنید.')
        InventoryLot.objects.create(product_variant=variant, quantity_received=quantity,
            quantity_remaining=quantity, unit_cost=unit_cost, note='ورود از فرم ساده سکه و پک')
        InventoryMovement.objects.create(product_variant=variant, type='purchase', quantity=quantity)
        variant.stock += quantity
        variant.save(update_fields=['stock'])
        listing.variant = variant


def sale_permissions(user, model):
    for obj in (Product, ProductVariant, model):
        check(user, obj, 'add')


def image_permissions(user):
    for obj in (ProductVariantImage, m.CoinImageDetail):
        check(user, obj, 'add')


def new_variant(name, price, description=''):
    token = uuid4().hex
    product = Product.objects.create(name=name, slug='coin-'+token, base_price=price,
        description=description, is_active=True)
    return ProductVariant.objects.create(product=product, sku='coin-'+token, price=price, stock=0)


def error(form, exc):
    # Model field names often belong to internal records, so show readable messages.
    form.add_error(None, ' / '.join(exc.messages) if isinstance(exc, ValidationError)
        else 'اطلاعات هم‌زمان تغییر کرده یا رکورد تکراری است. صفحه را دوباره باز کنید.')


@staff_member_required(login_url='admin:login')
@require_http_methods(['GET', 'POST'])
@csrf_protect
def register_pack(request):
    check(request.user, m.CoinPack, 'add')
    form = PackForm(request.POST or None, request.FILES or None)
    items = PackItems(request.POST or None, request.FILES or None, prefix='items')
    if request.method == 'POST':
        valid = form.is_valid()
        valid_items = items.is_valid()
        if valid and valid_items:
            d = form.cleaned_data
            rows = [f.cleaned_data for f in items if f.cleaned_data and not f.cleaned_data.get('DELETE')]
            if not rows:
                form.add_error(None, 'حداقل یک سکه به محتویات پک اضافه کنید.')
            seen = set()
            for row in rows:
                issue = row['issue']
                if issue.pk in seen:
                    form.add_error(None, 'هر سکه داخل پک را یک‌بار انتخاب و تعدادش را وارد کنید.')
                seen.add(issue.pk)
                if issue.year != d['year'] or issue.calendar != d['calendar'] or issue.date_status != 'known':
                    form.add_error(None, f'سال و تقویم «{issue}» با پک هماهنگ نیست.')
                if d['issuer'] and issue.coin_type.issuer_id != d['issuer'].pk:
                    form.add_error('issuer', 'کشور یکی از سکه‌های پک متفاوت است؛ برای پک چندکشوری کشور را خالی بگذارید.')
            if not form.errors:
                try:
                    with transaction.atomic():
                        sale_permissions(request.user, m.CoinPackVariant)
                        if rows:
                            check(request.user, m.CoinPackItem, 'add')
                        variant = new_variant(d['name'], d['price'], d['description'])
                        pack = m.CoinPack.objects.create(product=variant.product, issuer=d['issuer'],
                            year=d['year'], calendar=d['calendar'], description=d['description'])
                        listing = m.CoinPackVariant.objects.create(pack=pack, variant=variant, sale_mode=d['sale_mode'])
                        if d['photo']:
                            image_permissions(request.user)
                            upload(listing, d['photo'], 'pack')
                        for row in rows:
                            item = m.CoinPackItem.objects.create(pack_variant=listing, issue=row['issue'], quantity=row['quantity'])
                            for side in ('obverse', 'reverse'):
                                if row.get(side):
                                    image_permissions(request.user)
                                    upload(listing, row[side], side, item)
                        enter_stock(request.user, listing, d['quantity'] or 0, d['unit_cost'])
                    messages.success(request, 'پک ذخیره شد. وضعیت آمادگی فروش در همین صفحه مشخص است.')
                    return redirect(NS+'simple-sale', kind='pack', pk=listing.pk)
                except (ValidationError, IntegrityError) as exc:
                    error(form, exc)
    return render(request, 'coins/dashboard/simple_pack.html', context(request, form=form, items=items))


@staff_member_required(login_url='admin:login')
@require_http_methods(['GET', 'POST'])
@csrf_protect
def sale(request, kind, pk):
    from django import forms
    from django.http import Http404
    if kind not in ('coin', 'pack'):
        raise Http404
    model = m.CoinSpecimen if kind == 'coin' else m.CoinPackVariant
    listing = get_object_or_404(model.objects.select_related('variant__product'), pk=pk)
    check(request.user, model, 'change')
    class SaleForm(forms.Form):
        price = forms.DecimalField(label='قیمت فروش (تومان)', max_digits=12, decimal_places=0, min_value=0)
        quantity = forms.IntegerField(label='تعداد ورودی جدید (برای تغییر ندادن موجودی خالی بگذارید)', min_value=0, required=False)
        unit_cost = forms.DecimalField(label='بهای خرید هر واحد ورودی (تومان)', max_digits=14, decimal_places=0, min_value=0, required=False)
        def clean(self):
            d = super().clean()
            if d.get('quantity') and d.get('unit_cost') is None:
                self.add_error('unit_cost', 'بهای خرید را وارد کنید.')
            return d
    form = SaleForm(request.POST or None, request.FILES or None, initial={'price':listing.variant.price})
    targets = [(None, 'obverse', 'روی سکه'), (None, 'reverse', 'پشت سکه')]
    if kind == 'pack':
        targets = [(None, 'pack', 'نمای کامل پک')]
        for item in listing.items.select_related('issue__coin_type'):
            targets.extend([(item, 'obverse', f'روی {item.issue}'), (item, 'reverse', f'پشت {item.issue}')])
    photo_fields = []
    for item, side, label in targets:
        key = f'photo_{item.pk if item else 0}_{side}'
        form.fields[key] = forms.ImageField(label=label, required=False)
        photo_fields.append((key, item, side))
    if request.method == 'POST' and form.is_valid():
        action = request.POST.get('action', 'save')
        try:
            with transaction.atomic():
                variant = ProductVariant.objects.select_for_update().get(pk=listing.variant_id)
                listing = model.objects.select_for_update().get(pk=listing.pk)
                listing.variant = variant
                check(request.user, ProductVariant, 'change')
                variant.price = form.cleaned_data['price']
                # Explicitly clear an old discount so it cannot override the displayed sale price.
                variant.discount_price = None
                variant.save(update_fields=['price', 'discount_price'])
                for key, item, side in photo_fields:
                    if form.cleaned_data.get(key):
                        image_permissions(request.user)
                        upload(listing, form.cleaned_data[key], side, item)
                enter_stock(request.user, listing, form.cleaned_data['quantity'] or 0, form.cleaned_data['unit_cost'])
                if action == 'publish':
                    set_publication(listing, True)
                elif action == 'unpublish':
                    set_publication(listing, False)
            messages.success(request, 'تغییرات ذخیره شد.')
            return redirect(NS+'simple-sale', kind=kind, pk=pk)
        except (ValidationError, IntegrityError) as exc:
            error(form, exc)
            listing.refresh_from_db()
            listing.variant.refresh_from_db()
    return render(request, 'coins/dashboard/simple_sale.html', context(request, form=form,
        listing=listing, kind=kind, readiness=readiness_errors(listing),
        photos=listing.variant.images.all(), optional_photos=kind == 'pack'))


@staff_member_required(login_url='admin:login')
@require_http_methods(['GET'])
def sales(request):
    from django.db.models import Q
    from django.core.paginator import Paginator
    from django.core.exceptions import PermissionDenied
    from .dashboard_views import allowed
    rows = []
    permitted = False
    q = request.GET.get('q', '').strip()[:120]
    for model, kind in ((m.CoinSpecimen, 'coin'), (m.CoinPackVariant, 'pack')):
        if not allowed(request.user, model, 'view'):
            continue
        permitted = True
        qs = model.objects.select_related('variant__product').order_by('-created_at')
        if q:
            qs = qs.filter(Q(variant__product__name__icontains=q) | Q(variant__sku__icontains=q))
        rows.extend({'obj':obj,'kind':kind,'can_edit':allowed(request.user,model,'change')} for obj in qs)
    if not permitted:
        raise PermissionDenied
    rows.sort(key=lambda row:row['obj'].created_at, reverse=True)
    page = Paginator(rows, 30).get_page(request.GET.get('page'))
    return render(request, 'coins/dashboard/simple_sales.html', context(request,page=page,q=q))


@staff_member_required(login_url='admin:login')
@require_http_methods(['POST'])
@csrf_protect
def delete_photo(request, kind, pk, photo_pk):
    from django.http import Http404
    from products.signals.files import cleanup_variant_image_file
    if kind == 'catalog':
        check(request.user, m.CoinType, 'change')
        check(request.user, m.CoinCatalogImage, 'delete')
        with transaction.atomic():
            coin = get_object_or_404(m.CoinType.objects.select_for_update(), pk=pk)
            photo = get_object_or_404(m.CoinCatalogImage, pk=photo_pk, coin_type=coin)
            file = photo.image
            photo.delete()
            if file:
                cleanup_variant_image_file(file.storage, file.name)
        messages.success(request, 'عکس از کاتالوگ حذف شد.')
        return redirect(NS+'detail', pk=pk)
    model = {'coin':m.CoinSpecimen, 'pack':m.CoinPackVariant}.get(kind)
    if model is None:
        raise Http404
    check(request.user, model, 'change')
    check(request.user, ProductVariantImage, 'delete')
    with transaction.atomic():
        # Use the same lock order as sale updates.
        parent = get_object_or_404(model, pk=pk)
        ProductVariant.objects.select_for_update().get(pk=parent.variant_id)
        listing = get_object_or_404(model.objects.select_for_update(), pk=pk)
        photo = get_object_or_404(ProductVariantImage, pk=photo_pk, variant_id=listing.variant_id)
        was_main = photo.is_main
        photo.delete()
        if was_main:
            replacement = listing.variant.images.order_by('pk').first()
            if replacement:
                replacement.is_main = True
                replacement.save(update_fields=['is_main'])
        stopped = listing.is_published and bool(readiness_errors(listing))
        if stopped:
            set_publication(listing, False)
    messages.success(request, 'عکس حذف شد. فروش به علت ناقص شدن عکس‌های لازم به پیش‌نویس برگشت.' if stopped else 'عکس حذف شد.')
    return redirect(NS+'simple-sale', kind=kind, pk=pk)
