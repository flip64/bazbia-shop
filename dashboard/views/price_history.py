# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def price_history_list(request):
    """
    نمایش تاریخچه تغییرات قیمت.
    """

    context = {
        "page_title": "تاریخچه قیمت",
    }

    return render(
        request,
        "dashboard/pages/price_history.html",
        context,
    )


@login_required
def offer_price_history(request, offer_id):
    """
    نمایش تاریخچه قیمت یک پیشنهاد تأمین‌کننده.
    """

    context = {
        "page_title": "تاریخچه قیمت محصول",
        "offer_id": offer_id,
    }

    return render(
        request,
        "dashboard/pages/offer_price_history.html",
        context,
    )