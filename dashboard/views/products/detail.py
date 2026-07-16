# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render




@login_required
def product_detail(request, pk):
    """
    نمایش جزئیات کامل یک محصول.

    اطلاعات بارگذاری‌شده:
    - اطلاعات اصلی محصول
    - دسته‌بندی
    - تگ‌ها
    - تصاویر و ویدئوها
    - مشخصات
    - واریانت‌ها
    - ویژگی‌ها و تصاویر هر واریانت
    - پیشنهادهای تأمین‌کنندگان
    - ۱۰ رکورد آخر تاریخچه قیمت خرید
    """

    supplier_offers_queryset = (
        SupplierOffer.objects
        .select_related("supplier")
        .order_by("-is_primary", "supplier__name")
    )

    variants_queryset = (
        ProductVariant.objects
        .prefetch_related(
            "attributes__attribute",
            "images",
            Prefetch(
                "supplier_offers",
                queryset=supplier_offers_queryset,
            ),
        )
        .order_by("id")
    )

    product = get_object_or_404(
        Product.objects
        .select_related("category")
        .prefetch_related(
            "tags",
            "images",
            "videos",
            "specifications",
            Prefetch(
                "variants",
                queryset=variants_queryset,
            ),
        ),
        pk=pk,
    )

    price_history = (
        SupplierPriceHistory.objects
        .filter(
            supplier_offer__variant__product=product,
        )
        .select_related(
            "supplier_offer",
            "supplier_offer__supplier",
            "supplier_offer__variant",
        )
        .order_by("-created_at")[:10]
    )

    context = {
        "page_title": f"جزئیات محصول: {product.name}",
        "product": product,
        "price_history": price_history,
    }

    return render(
        request,
        "dashboard/pages/product_detail.html",
        context,
    )
