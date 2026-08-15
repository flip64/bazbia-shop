# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render

from products.models import Product, ProductVariant
from suppliers.models import SupplierOffer, SupplierPriceHistory


@login_required
def product_list(request):
    """
    نمایش لیست تمام محصولات.
    """

    context = {
        "page_title": "همه محصولات",
    }

    return render(
        request,
        "dashboard/pages/product_list.html",
        context,
    )


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


@login_required
def product_edit(request, pk):
    """
    ویرایش یک محصول.
    """

    context = {
        "page_title": "ویرایش محصول",
        "product_id": pk,
    }

    return render(
        request,
        "dashboard/pages/product_edit.html",
        context,
    )


@login_required
def product_profit_manager(request):
    """
    مدیریت گروهی درصد سود محصولات.
    """

    context = {
        "page_title": "مدیریت درصد سود",
    }

    return render(
        request,
        "dashboard/pages/product_profit.html",
        context,
    )


@login_required
def product_price_manager(request):
    """
    مدیریت قیمت فروش محصولات.
    """

    context = {
        "page_title": "مدیریت قیمت فروش",
    }

    return render(
        request,
        "dashboard/pages/product_price.html",
        context,
    )