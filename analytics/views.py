# analytics/views.py

from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from analytics.models import SiteEvent


@staff_member_required
def analytics_dashboard(request):
    now = timezone.localtime()

    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    yesterday_start = today_start - timedelta(days=1)
    last_7_days = today_start - timedelta(days=6)
    last_30_days = today_start - timedelta(days=29)

    page_views = SiteEvent.objects.filter(
        event_type=SiteEvent.EventType.PAGE_VIEW,
    )

    # امروز
    today_views = page_views.filter(
        created_at__gte=today_start,
    ).count()

    today_unique_visitors = (
        page_views
        .filter(created_at__gte=today_start)
        .exclude(visitor_id="")
        .values("visitor_id")
        .distinct()
        .count()
    )

    # دیروز
    yesterday_views = page_views.filter(
        created_at__gte=yesterday_start,
        created_at__lt=today_start,
    ).count()

    # 7 روز اخیر
    last_7_days_views = page_views.filter(
        created_at__gte=last_7_days,
    ).count()

    last_7_days_unique = (
        page_views
        .filter(created_at__gte=last_7_days)
        .exclude(visitor_id="")
        .values("visitor_id")
        .distinct()
        .count()
    )

    # 30 روز اخیر
    last_30_days_views = page_views.filter(
        created_at__gte=last_30_days,
    ).count()

    # صفحات پربازدید
    top_pages = (
        page_views
        .filter(created_at__gte=last_7_days)
        .values("path")
        .annotate(views=Count("id"))
        .order_by("-views")[:10]
    )

    # منابع ورودی
    traffic_sources = (
        page_views
        .filter(created_at__gte=last_7_days)
        .values("source")
        .annotate(views=Count("id"))
        .order_by("-views")
    )

    # مشاهده محصولات
    product_views = SiteEvent.objects.filter(
        event_type=SiteEvent.EventType.PRODUCT_VIEW,
        created_at__gte=last_7_days,
    ).count()

    # افزودن به سبد
    add_to_cart_count = SiteEvent.objects.filter(
        event_type=SiteEvent.EventType.ADD_TO_CART,
        created_at__gte=last_7_days,
    ).count()

    context = {
        "today_views": today_views,
        "today_unique_visitors": today_unique_visitors,

        "yesterday_views": yesterday_views,

        "last_7_days_views": last_7_days_views,
        "last_7_days_unique": last_7_days_unique,

        "last_30_days_views": last_30_days_views,

        "product_views": product_views,
        "add_to_cart_count": add_to_cart_count,

        "top_pages": top_pages,
        "traffic_sources": traffic_sources,
    }

    return render(
        request,
        "analytics/dashboard.html",
        context,
    )
