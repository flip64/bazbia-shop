# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from suppliers.models import Supplier, SupplierOffer
from django.core.paginator import Paginator
from django.db.models import Q


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
def supplier_products(request, slug):
    """
    نمایش محصولات یک تأمین‌کننده همراه با:
    - جستجو
    - فیلتر موجودی
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
    stock_status = request.GET.get("stock", "").strip()

    if search_query:
        product_offers = product_offers.filter(
            Q(variant__product__name__icontains=search_query)
            | Q(variant__sku__icontains=search_query)
        )

    if stock_status == "available":
        product_offers = product_offers.filter(
            supplier_stock__gt=0,
        )

    elif stock_status == "unavailable":
        product_offers = product_offers.filter(
            supplier_stock__lte=0,
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
    }

    return render(
        request,
        "dashboard/pages/supplier_products.html",
        context,
    )
