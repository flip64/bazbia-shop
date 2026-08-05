from django.contrib import messages
from django.contrib.admin.views.decorators import (
    staff_member_required,
)
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from products.models import ProductVariant
from products.services.variant_stock import (
    VariantStockService,
)
from torob_integration.models import (
    TorobVariantConfig,
)


@staff_member_required
def torob_variant_management(request):
    """
    صفحه مدیریت واریانت‌های قابل نمایش در ترب.

    موجودی قابل عرضه:
        موجودی داخلی بازبیا
        +
        موجودی معتبر تأمین‌کنندگان
    """

    if request.method == "POST":
        return handle_torob_management_action(
            request
        )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    torob_status = request.GET.get(
        "torob_status",
        "",
    ).strip()

    stock_status = request.GET.get(
        "stock_status",
        "",
    ).strip()

    # اضافه‌کردن موجودی ترکیبی به QuerySet
    queryset = VariantStockService.annotate(
        ProductVariant.objects.all()
    )

    queryset = (
        queryset
        .select_related(
            "product",
            "product__category",
            "torob_config",
        )
        .prefetch_related(
            "attributes__attribute",
            "images",
            "product__images",
        )
        .order_by(
            "product__name",
            "id",
        )
    )

    # جستجو
    if search:
        search_filter = (
            Q(
                product__name__icontains=search
            )
            | Q(
                sku__icontains=search
            )
        )

        try:
            search_filter |= Q(
                id=int(search)
            )
        except (TypeError, ValueError):
            pass

        queryset = queryset.filter(
            search_filter
        )

    # فیلتر وضعیت انتشار در ترب
    if torob_status == "enabled":
        queryset = queryset.filter(
            torob_config__is_enabled=True
        )

    elif torob_status == "disabled":
        queryset = queryset.filter(
            Q(
                torob_config__is_enabled=False
            )
            | Q(
                torob_config__isnull=True
            )
        )

    # فیلتر وضعیت قابل فروش بودن
    if stock_status == "available":
        queryset = queryset.filter(
            available_stock__gt=0,
            price__gt=0,
            product__is_active=True,
        )

    elif stock_status == "unavailable":
        queryset = queryset.filter(
            Q(
                available_stock__lte=0
            )
            | Q(
                price__lte=0
            )
            | Q(
                product__is_active=False
            )
        )

    queryset = queryset.distinct()

    paginator = Paginator(
        queryset,
        50,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    variant_rows = []

    for variant in page_obj.object_list:
        config = getattr(
            variant,
            "torob_config",
            None,
        )

        # این روابط قبلاً Prefetch شده‌اند
        variant_images = list(
            variant.images.all()
        )

        product_images = list(
            variant.product.images.all()
        )

        has_image = bool(
            variant_images
            or product_images
        )

        internal_stock = int(
            variant.stock or 0
        )

        supplier_stock = int(
            variant.supplier_available_stock
            or 0
        )

        available_stock = int(
            variant.available_stock
            or 0
        )

        is_eligible = (
            available_stock > 0
            and variant.price > 0
            and variant.product.is_active
            and has_image
        )

        attributes_text = "، ".join(
            str(attribute)
            for attribute
            in variant.attributes.all()
        )

        variant_rows.append(
            {
                "variant": variant,
                "config": config,
                "is_enabled": bool(
                    config
                    and config.is_enabled
                ),
                "is_eligible": is_eligible,
                "has_image": has_image,
                "attributes_text": (
                    attributes_text
                ),

                # اطلاعات موجودی
                "internal_stock": (
                    internal_stock
                ),
                "supplier_stock": (
                    supplier_stock
                ),
                "available_stock": (
                    available_stock
                ),
            }
        )

    enabled_count = (
        TorobVariantConfig.objects
        .filter(
            is_enabled=True
        )
        .count()
    )

    # شمارش واریانت‌های واجد شرایط
    eligible_queryset = (
        VariantStockService.annotate(
            ProductVariant.objects.all()
        )
        .filter(
            available_stock__gt=0,
            price__gt=0,
            product__is_active=True,
        )
        .filter(
            Q(
                images__isnull=False
            )
            | Q(
                product__images__isnull=False
            )
        )
        .distinct()
    )

    eligible_count = (
        eligible_queryset.count()
    )

    context = {
        "title": (
            "مدیریت محصولات ترب"
        ),
        "page_obj": page_obj,
        "variant_rows": variant_rows,
        "search": search,
        "torob_status": torob_status,
        "stock_status": stock_status,
        "enabled_count": enabled_count,
        "eligible_count": eligible_count,
        "filtered_count": paginator.count,
    }

    return render(
        request,
        (
            "dashboard/torob/"
            "variant_management.html"
        ),
        context,
    )


@staff_member_required
@transaction.atomic
def handle_torob_management_action(
    request,
):
    """
    فعال یا غیرفعال‌کردن گروهی واریانت‌ها.

    برای فعال‌شدن، واریانت باید:

    - موجودی ترکیبی بیشتر از صفر داشته باشد.
    - قیمت بیشتر از صفر داشته باشد.
    - محصول اصلی فعال باشد.
    - حداقل یک تصویر داشته باشد.
    """

    action = request.POST.get(
        "action",
        "",
    ).strip()

    selected_values = (
        request.POST.getlist(
            "selected_variants"
        )
    )

    if action not in {
        "enable",
        "disable",
    }:
        messages.error(
            request,
            "عملیات انتخاب‌شده معتبر نیست.",
        )

        return redirect(
            "dashboard:torob-variants"
        )

    variant_ids = []

    for value in selected_values:
        try:
            variant_id = int(value)
        except (TypeError, ValueError):
            continue

        if variant_id > 0:
            variant_ids.append(
                variant_id
            )

    # حذف شناسه‌های تکراری
    variant_ids = list(
        dict.fromkeys(variant_ids)
    )

    if not variant_ids:
        messages.warning(
            request,
            "هیچ واریانتی انتخاب نشده است.",
        )

        return redirect(
            "dashboard:torob-variants"
        )

    variants = VariantStockService.annotate(
        ProductVariant.objects.filter(
            id__in=variant_ids
        )
    )

    variants = (
        variants
        .select_related(
            "product"
        )
        .prefetch_related(
            "images",
            "product__images",
        )
    )

    changed_count = 0
    skipped_count = 0

    now = timezone.now()

    for variant in variants:
        config, _ = (
            TorobVariantConfig.objects
            .get_or_create(
                variant=variant,
                defaults={
                    "page_unique": str(
                        variant.id
                    ),
                    "torob_updated_at": now,
                },
            )
        )

        if action == "enable":
            # روابط تصاویر Prefetch شده‌اند
            variant_images = list(
                variant.images.all()
            )

            product_images = list(
                variant.product.images.all()
            )

            has_image = bool(
                variant_images
                or product_images
            )

            available_stock = int(
                variant.available_stock
                or 0
            )

            is_eligible = (
                available_stock > 0
                and variant.price > 0
                and variant.product.is_active
                and has_image
            )

            if not is_eligible:
                skipped_count += 1
                continue

            new_status = True

        else:
            new_status = False

        if (
            config.is_enabled
            == new_status
        ):
            continue

        config.is_enabled = new_status
        config.torob_updated_at = now

        config.save(
            update_fields=[
                "is_enabled",
                "torob_updated_at",
                "updated_at",
            ]
        )

        changed_count += 1

    if changed_count:
        messages.success(
            request,
            (
                f"{changed_count} واریانت "
                "با موفقیت به‌روزرسانی شد."
            ),
        )
    else:
        messages.info(
            request,
            "هیچ تغییری اعمال نشد.",
        )

    if skipped_count:
        messages.warning(
            request,
            (
                f"{skipped_count} واریانت "
                "به دلیل موجودی قابل عرضه، "
                "قیمت، تصویر یا وضعیت محصول "
                "فعال نشد."
            ),
        )

    return redirect(
        "dashboard:torob-variants"
    )
