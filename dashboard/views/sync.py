# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def sync_dashboard(request):
    """
    صفحه مدیریت همگام‌سازی تأمین‌کنندگان.
    """

    context = {
        "page_title": "همگام‌سازی",
    }

    return render(
        request,
        "dashboard/pages/sync.html",
        context,
    )