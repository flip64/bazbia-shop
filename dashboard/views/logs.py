# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def operation_logs(request):
    """
    نمایش گزارش عملیات و خطاها.
    """

    context = {
        "page_title": "گزارش عملیات",
    }

    return render(
        request,
        "dashboard/pages/logs.html",
        context,
    )