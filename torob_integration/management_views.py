from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from products.models import ProductVariant
from torob_integration.models import TorobVariantConfig


@staff_member_required
def torob_variant_management(request):
    """
    صفحه مدیریت واریانت‌های قابل نمایش در ترب.
    """

    queryset = (
        ProductVariant.objects
        .select_related(
            "product",
            "product__category",
        )
        .prefetch_related(
            "attributes__attribute",
            "product__images",
            "images",
        )
        .order_by(
            "product__name",
            "id",
        )
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

    if search:
        queryset = queryset.filter(
            Q(product__name__icontains=search)
            | Q(sku__icontains=search)
            | Q(id__icontains=search)
        )

    if torob_status == "enabled":
        queryset = queryset.filter(
            torob_config__is_enabled=True
        )

    elif torob_status == "disabled":
        queryset = queryset.filter(
            Q(torob_config__is_enabled=False)
            | Q(torob_config__isnull=True)
        )

    if stock_status == "available":
        queryset = queryset.filter(
            stock__gt=0,
            price__gt=0,
            product__is_active=True,
        )

    elif stock_status == "unavailable":
        queryset = queryset.filter(
            Q(stock__lte=0)
            | Q(price__lte=0)
            | Q(product__is_active=False)
        )

    if request.method == "POST":
        return handle_torob_management_action(
            request
        )

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

        variant_rows.append(
            {
                "variant": variant,
                "config": config,
                "is_enabled": bool(
                    config and config.is_enabled
                ),
                "is_eligible": (
                    variant.stock > 0
                    and variant.price > 0
                    and variant.product.is_active
                ),
                "has_variant_image": (
                    len(variant.images.all()) > 0
                ),
                "has_product_image": (
                    len(variant.product.images.all()) > 0
                ),
            }
        )

    context = {
        "title": "مدیریت محصولات ترب",
        "page_obj": page_obj,
        "variant_rows": variant_rows,
        "search": search,
        "torob_status": torob_status,
        "stock_status": stock_status,
        "enabled_count": (
            TorobVariantConfig.objects.filter(
                is_enabled=True
            ).count()
        ),
        "total_count": queryset.count(),
    }

    return render(
        request,
        "torob_integration/variant_management.html",
        context,
    )


@staff_member_required
@transaction.atomic
def handle_torob_management_action(request):
    """
    فعال یا غیرفعال‌کردن گروهی واریانت‌ها.
    """

    action = request.POST.get(
        "action",
        "",
    ).strip()

    selected_ids = request.POST.getlist(
        "selected_variants"
    )

    valid_actions = {
        "enable",
        "disable",
    }

    if action not in valid_actions:
        messages.error(
            request,
            "عملیات انتخاب‌شده معتبر نیست.",
        )
        return redirect(
            "torob_management:variants"
        )

    variant_ids = []

    for value in selected_ids:
        try:
            variant_ids.append(
                int(value)
            )
        except (TypeError, ValueError):
            continue

    if not variant_ids:
        messages.warning(
            request,
            "هیچ واریانتی انتخاب نشده است.",
        )
        return redirect(
            "torob_management:variants"
        )

    variants = ProductVariant.objects.filter(
        id__in=variant_ids
    )

    changed_count = 0
    skipped_count = 0
    now = timezone.now()

    for variant in variants:
        config, _ = (
            TorobVariantConfig.objects.get_or_create(
                variant=variant,
                defaults={
                    "page_unique": str(variant.id),
                    "torob_updated_at": now,
                },
            )
        )

        if action == "enable":
            is_eligible = (
                variant.stock > 0
                and variant.price > 0
                and variant.product.is_active
            )

            if not is_eligible:
                skipped_count += 1
                continue

            config.is_enabled = True

        else:
            config.is_enabled = False

        config.torob_updated_at = now

        config.save(
            update_fields=[
                "is_enabled",
                "torob_updated_at",
                "updated_at",
            ]
        )

        changed_count += 1

    messages.success(
        request,
        f"{changed_count} واریانت بروزرسانی شد.",
    )

    if skipped_count:
        messages.warning(
            request,
            (
                f"{skipped_count} واریانت به دلیل "
                "ناموجود بودن، قیمت نامعتبر یا "
                "غیرفعال بودن محصول فعال نشد."
            ),
        )

    return redirect(
        "torob_management:variants"
)
