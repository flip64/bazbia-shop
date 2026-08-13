# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


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
    نمایش جزئیات یک محصول.
    """

    context = {
        "page_title": "جزئیات محصول",
        "product_id": pk,
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