from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from core.logging_config import get_logger
from core.sync_tracker import SyncRun
from products.models import Product

from basalam_integration.models import BasalamProductMapping
from basalam_integration.services.client import BasalamAPIError, BasalamClient
from basalam_integration.services.product_service import (
    publish_product_to_basalam,
    set_product_active_on_basalam,
    sync_product_to_basalam,
    zero_product_stock_on_basalam,
)


logger = get_logger(__name__)


def _product_image_url(product):
    images = list(product.images.all())
    image = next((item for item in images if item.is_main), None)
    image = image or (images[0] if images else None)
    if image and image.image:
        try:
            return image.image.url
        except (ValueError, OSError):
            pass
    return (image.source_url if image else "") or ""


def _remote_products_for_page(products):
    remote_ids = []
    for product in products:
        try:
            mapping = product.basalam_mapping
        except BasalamProductMapping.DoesNotExist:
            continue
        if mapping.is_active:
            remote_ids.append(mapping.basalam_product_id)
    if not remote_ids:
        return {}

    vendor_id = str(settings.BASALAM_VENDOR_ID).strip()
    if not vendor_id.isdigit():
        raise ImproperlyConfigured(
            "BASALAM_VENDOR_ID باید یک شناسه عددی معتبر باشد."
        )
    response = BasalamClient().get_vendor_products(
        vendor_id=int(vendor_id),
        product_ids=remote_ids,
        per_page=max(len(remote_ids), 1),
    )
    data = response.get("data") or response.get("result") or []
    if isinstance(data, dict):
        data = data.get("data") or data.get("products") or []
    return {
        int(item["id"]): item
        for item in data
        if isinstance(item, dict) and item.get("id")
    }


@staff_member_required
def basalam_product_management(request):
    if request.method == "POST":
        return _handle_basalam_action(request)

    queryset = (
        Product.objects.select_related("category", "basalam_mapping")
        .prefetch_related(
            "images",
            "variants__attributes__attribute",
            "basalam_mapping__variation_mappings",
        )
        .annotate(variant_count=Count("variants", distinct=True))
        .order_by("-updated_at")
    )

    search = request.GET.get("search", "").strip()
    connection = request.GET.get("connection", "").strip()
    local_status = request.GET.get("local_status", "").strip()

    if search:
        search_filter = (
            Q(name__icontains=search)
            | Q(slug__icontains=search)
            | Q(variants__sku__icontains=search)
        )
        if search.isdigit():
            search_filter |= Q(pk=int(search)) | Q(
                basalam_mapping__basalam_product_id=int(search)
            )
        queryset = queryset.filter(search_filter).distinct()
    if connection == "connected":
        queryset = queryset.filter(
            basalam_mapping__isnull=False,
            basalam_mapping__is_active=True,
        )
    elif connection == "unconnected":
        queryset = queryset.filter(
            Q(basalam_mapping__isnull=True)
            | Q(basalam_mapping__is_active=False)
        )
    else:
        connection = ""
    if local_status == "active":
        queryset = queryset.filter(is_active=True)
    elif local_status == "inactive":
        queryset = queryset.filter(is_active=False)
    else:
        local_status = ""

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    products = list(page_obj.object_list)

    remote_products = {}
    remote_error = ""
    if request.GET.get("refresh") == "1":
        try:
            remote_products = _remote_products_for_page(products)
        except (BasalamAPIError, ImproperlyConfigured) as exc:
            remote_error = str(exc)
            messages.error(request, f"دریافت وضعیت باسلام ناموفق بود: {exc}")

    for product in products:
        product.dashboard_image_url = _product_image_url(product)
        try:
            mapping = product.basalam_mapping
        except BasalamProductMapping.DoesNotExist:
            mapping = None
        product.remote_data = (
            remote_products.get(mapping.basalam_product_id)
            if mapping
            else None
        )
        if product.remote_data:
            remote_status = product.remote_data.get("status")
            if isinstance(remote_status, dict):
                product.remote_status = (
                    remote_status.get("name")
                    or remote_status.get("title")
                    or str(remote_status.get("value") or "")
                )
            else:
                product.remote_status = str(remote_status or "نامشخص")
            remote_variants = (
                product.remote_data.get("variants")
                or product.remote_data.get("variant")
                or []
            )
            product.remote_stock = sum(
                int(item.get("stock") or 0)
                for item in remote_variants
                if isinstance(item, dict)
            )
            if not remote_variants:
                product.remote_stock = int(
                    product.remote_data.get("stock")
                    or product.remote_data.get("inventory")
                    or 0
                )

    connected_count = Product.objects.filter(
        basalam_mapping__is_active=True
    ).count()
    context = {
        "page_title": "مدیریت محصولات باسلام",
        "products": products,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "search": search,
        "connection": connection,
        "local_status": local_status,
        "remote_refreshed": request.GET.get("refresh") == "1" and not remote_error,
        "query_without_page": "&".join(
            f"{key}={value}"
            for key, value in request.GET.items()
            if key != "page"
        ),
        "statistics": {
            "all": Product.objects.count(),
            "connected": connected_count,
            "unconnected": Product.objects.count() - connected_count,
        },
    }
    return render(
        request,
        "dashboard/pages/basalam/product_list.html",
        context,
    )


def _handle_basalam_action(request):
    product = get_object_or_404(
        Product.objects.select_related("category", "basalam_mapping")
        .prefetch_related(
            "images",
            "variants__attributes__attribute",
            "basalam_mapping__variation_mappings",
        ),
        pk=request.POST.get("product_id"),
    )
    action = request.POST.get("action", "").strip()

    with SyncRun(name=f"dashboard_basalam_{action}", supplier="basalam") as sync:
        sync.stats.received = 1
        try:
            if action in {"add_draft", "add_publish"}:
                result = publish_product_to_basalam(
                    product,
                    published=action == "add_publish",
                )
                sync.stats.created = 1
                messages.success(
                    request,
                    f"محصول با شناسه {result.basalam_product_id} به باسلام اضافه شد.",
                )
            elif action == "sync":
                result = sync_product_to_basalam(product)
                sync.stats.created = result.added_count
                sync.stats.updated = result.updated_count
                messages.success(
                    request,
                    "محصول همگام شد؛ "
                    f"{result.added_count} واریانت اضافه و "
                    f"{result.updated_count} واریانت به‌روزرسانی شد.",
                )
            elif action == "activate":
                sync_product_to_basalam(product)
                set_product_active_on_basalam(product, active=True)
                sync.stats.updated = 1
                messages.success(request, "محصول در باسلام فعال و همگام شد.")
            elif action == "deactivate":
                result = set_product_active_on_basalam(
                    product,
                    active=False,
                    fallback_to_zero_stock=True,
                )
                sync.stats.updated = 1
                if result.stock_zero_fallback:
                    messages.warning(
                        request,
                        "غیرفعال‌سازی پذیرفته نشد؛ موجودی محصول در باسلام صفر شد.",
                    )
                else:
                    messages.success(request, "محصول در باسلام غیرفعال شد.")
            elif action == "zero_stock":
                count = zero_product_stock_on_basalam(product)
                sync.stats.updated = count
                messages.success(
                    request,
                    f"موجودی {count} واریانت در باسلام صفر شد.",
                )
            else:
                raise ValidationError("عملیات انتخاب‌شده معتبر نیست.")

            logger.info(
                "عملیات داشبورد باسلام انجام شد | action=%s | product_id=%s",
                action,
                product.pk,
            )
        except (
            BasalamAPIError,
            ImproperlyConfigured,
            ValidationError,
            OSError,
            ValueError,
        ) as exc:
            sync.stats.failed += 1
            logger.exception(
                "عملیات داشبورد باسلام ناموفق بود | action=%s | product_id=%s",
                action,
                product.pk,
            )
            messages.error(request, str(exc))

    return redirect("dashboard:basalam_products")
