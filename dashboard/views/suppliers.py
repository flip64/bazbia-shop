# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from suppliers.models import Supplier, SupplierOffer


@login_required
def supplier_list(request):
    """
    نمایش لیست تأمین‌کنندگان.
    """

    context = {
        "page_title": "تأمین‌کنندگان",
    }

    return render(
        request,
        "dashboard/pages/supplier_list.html",
        context,
    )


@login_required
def supplier_detail(request, slug):
    """
    نمایش جزئیات یک تأمین‌کننده.
    """

    context = {
        "page_title": "جزئیات تأمین‌کننده",
        "supplier_slug": slug,
    }

    return render(
        request,
        "dashboard/pages/supplier_detail.html",
        context,
    )


@login_required
def supplier_products(request, slug):
    """
    نمایش محصولات یک تأمین‌کننده همراه با:
    - جستجو بر اساس نام محصول یا SKU
    - فیلتر وضعیت فعال یا غیرفعال محصول در سایت
    - صفحه‌بندی
    """

    supplier = get_object_or_404(
        Supplier,
        slug=slug,
        is_active=True,
    )

    suppliers = Supplier.objects.filter(
        is_active=True,
    ).order_by("name")

    product_offers = (
        SupplierOffer.objects
        .filter(supplier=supplier)
        .select_related(
            "supplier",
            "variant",
            "variant__product",
        )
        .order_by("variant__product__name")
    )

    search_query = request.GET.get("q", "").strip()
    site_status = request.GET.get("status", "").strip()

    if search_query:
        product_offers = product_offers.filter(
            Q(variant__product__name__icontains=search_query)
            | Q(variant__sku__icontains=search_query)
        )

    if site_status == "active":
        product_offers = product_offers.filter(
            variant__product__is_active=True,
        )

    elif site_status == "inactive":
        product_offers = product_offers.filter(
            variant__product__is_active=False,
        )

    paginator = Paginator(product_offers, 25)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_title": f"محصولات {supplier.name}",
        "supplier": supplier,
        "suppliers": suppliers,
        "product_offers": page_obj.object_list,
        "page_obj": page_obj,
        "total_results": paginator.count,
        "search_query": search_query,
        "site_status": site_status,
    }

    return render(
        request,
        "dashboard/pages/supplier_products.html",
        context,
    )
