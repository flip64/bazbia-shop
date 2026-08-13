# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


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
    نمایش محصولات یک تأمین‌کننده.
    """

    context = {
        "page_title": "محصولات تأمین‌کننده",
        "supplier_slug": slug,
    }

    return render(
        request,
        "dashboard/pages/supplier_products.html",
        context,
    )