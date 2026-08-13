# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from suppliers.models import Supplier


@login_required
def dashboard_home(request):
    """
    صفحه اصلی داشبورد مدیریت بازبیا.
    """

    suppliers = Supplier.objects.filter(is_active=True)

    context = {
        "page_title": "داشبورد",
        "suppliers": suppliers,
    }

    return render(
        request,
        "dashboard/pages/home.html",
        context,
    )