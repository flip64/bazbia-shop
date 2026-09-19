# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Exists, F, Max, Min, OuterRef, Prefetch, Q
from django.http import Http404
from django.shortcuts import render

from products.models import (
    Category,
    Product,
    ProductImage,
    ProductVariant,
    ProductVariantImage,
)
from suppliers.models import SupplierOffer


def _image_url(image):
    if not image:
        return ""
    if getattr(image, "image", None):
        try:
            return image.image.url
        except (ValueError, OSError):
            pass
    return getattr(image, "source_url", "") or ""


@login_required
def product_list(request):
    """فهرست مدیریتی محصولات با جست‌وجو، فیلتر و کنترل کیفیت."""

    if not request.user.is_staff:
        raise Http404

    available_variant = ProductVariant.objects.filter(
        product_id=OuterRef("pk")
    ).filter(
        Q(stock__gt=0)
        | Q(
            supplier_offers__is_available=True,
            supplier_offers__supplier_stock__gt=0,
        )
    )
    low_stock_variant = (
        ProductVariant.objects
        .filter(
            product_id=OuterRef("pk"),
            stock__gt=0,
            stock__lte=F("low_stock_threshold"),
        )
        .exclude(
            supplier_offers__is_available=True,
            supplier_offers__supplier_stock__gt=0,
        )
    )

    queryset = (
        Product.objects
        .select_related("category")
        .annotate(
            variant_count=Count("variants", distinct=True),
            minimum_price=Min("variants__price"),
            maximum_price=Max("variants__price"),
            has_available_variant=Exists(available_variant),
            has_low_stock_variant=Exists(low_stock_variant),
            has_product_image=Exists(
                ProductImage.objects.filter(product_id=OuterRef("pk"))
            ),
            has_variant_image=Exists(
                ProductVariantImage.objects.filter(
                    variant__product_id=OuterRef("pk")
                )
            ),
        )
    )

    search = request.GET.get("search", "").strip()
    selected_status = request.GET.get("status", "").strip()
    selected_stock = request.GET.get("stock", "").strip()
    selected_quality = request.GET.get("quality", "").strip()
    selected_category = request.GET.get("category", "").strip()
    selected_ordering = request.GET.get("ordering", "-updated_at").strip()

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(slug__icontains=search)
            | Q(variants__sku__icontains=search)
        ).distinct()

    if selected_status == "active":
        queryset = queryset.filter(is_active=True)
    elif selected_status == "inactive":
        queryset = queryset.filter(is_active=False)
    else:
        selected_status = ""

    if selected_stock == "available":
        queryset = queryset.filter(has_available_variant=True)
    elif selected_stock == "out_of_stock":
        queryset = queryset.filter(has_available_variant=False)
    elif selected_stock == "low_stock":
        queryset = queryset.filter(has_low_stock_variant=True)
    else:
        selected_stock = ""

    if selected_quality == "without_image":
        queryset = queryset.filter(
            has_product_image=False,
            has_variant_image=False,
        )
    elif selected_quality == "without_category":
        queryset = queryset.filter(category__isnull=True)
    elif selected_quality == "without_description":
        queryset = queryset.filter(Q(description="") | Q(description__isnull=True))
    elif selected_quality == "zero_price":
        queryset = queryset.filter(variants__price__lte=0).distinct()
    else:
        selected_quality = ""

    if selected_category.isdigit():
        queryset = queryset.filter(category_id=int(selected_category))
    else:
        selected_category = ""

    allowed_orderings = {
        "-updated_at",
        "updated_at",
        "name",
        "-name",
        "minimum_price",
        "-maximum_price",
        "-created_at",
        "created_at",
    }
    if selected_ordering not in allowed_orderings:
        selected_ordering = "-updated_at"

    paginator = Paginator(queryset.order_by(selected_ordering), 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    supplier_offers = SupplierOffer.objects.filter(
        is_available=True,
        supplier_stock__gt=0,
    ).select_related("supplier")
    variants = ProductVariant.objects.prefetch_related(
        "images",
        Prefetch("supplier_offers", queryset=supplier_offers),
    )
    products = list(
        page_obj.object_list.prefetch_related(
            "images",
            Prefetch("variants", queryset=variants),
        )
    )

    for product in products:
        product.internal_stock = sum(variant.stock for variant in product.variants.all())
        product.supplier_stock = sum(
            offer.supplier_stock
            for variant in product.variants.all()
            for offer in variant.supplier_offers.all()
        )
        product.available_stock = product.internal_stock + product.supplier_stock

        images = list(product.images.all())
        main_image = next((image for image in images if image.is_main), None)
        main_image = main_image or (images[0] if images else None)
        if not main_image:
            main_image = next(
                (
                    image
                    for variant in product.variants.all()
                    for image in variant.images.all()
                    if image.is_main
                ),
                None,
            )
        if not main_image:
            main_image = next(
                (
                    image
                    for variant in product.variants.all()
                    for image in variant.images.all()
                ),
                None,
            )
        product.dashboard_image_url = _image_url(main_image)

    query_params = request.GET.copy()
    query_params.pop("page", None)

    statistics = {
        "all": Product.objects.count(),
        "active": Product.objects.filter(is_active=True).count(),
        "inactive": Product.objects.filter(is_active=False).count(),
        "out_of_stock": Product.objects.annotate(
            available=Exists(available_variant)
        ).filter(available=False).count(),
        "without_image": Product.objects.annotate(
            product_image=Exists(
                ProductImage.objects.filter(product_id=OuterRef("pk"))
            ),
            variant_image=Exists(
                ProductVariantImage.objects.filter(
                    variant__product_id=OuterRef("pk")
                )
            ),
        ).filter(product_image=False, variant_image=False).count(),
    }

    context = {
        "page_title": "مدیریت محصولات",
        "products": products,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "statistics": statistics,
        "categories": Category.objects.order_by("name"),
        "search": search,
        "selected_status": selected_status,
        "selected_stock": selected_stock,
        "selected_quality": selected_quality,
        "selected_category": selected_category,
        "selected_ordering": selected_ordering,
        "query_without_page": query_params.urlencode(),
    }

    return render(request, "dashboard/pages/product_list.html", context)


@login_required
def product_profit_manager(request):
    if not request.user.is_staff:
        raise Http404

    context = {"page_title": "مدیریت درصد سود"}
    return render(request, "dashboard/pages/product_profit.html", context)


@login_required
def product_price_manager(request):
    if not request.user.is_staff:
        raise Http404

    context = {"page_title": "مدیریت قیمت فروش"}
    return render(request, "dashboard/pages/product_price.html", context)
