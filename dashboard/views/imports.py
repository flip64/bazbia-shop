# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def import_dashboard(request):
    """
    صفحه مدیریت ورود اطلاعات محصولات.
    """

    context = {
        "page_title": "ورود اطلاعات",
    }

    return render(
        request,
        "dashboard/pages/import.html",
        context,
    )