# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render





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
