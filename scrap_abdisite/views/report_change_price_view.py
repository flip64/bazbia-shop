# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from persiantools.jdatetime import JalaliDate
from scrap_abdisite.models import PriceHistory

def price_change_report(request):
    start_j = request.GET.get("start")
    end_j = request.GET.get("end")
    range_option = request.GET.get("range")  # "week", "month", "year"

    # 🟢 تعیین بازه پیش‌فرض (مثلاً هفته اخیر)
    today_g = timezone.now().date()
    if range_option == "week":
        start_g = today_g - timedelta(days=7)
    elif range_option == "month":
        start_g = today_g - timedelta(days=30)
    elif range_option == "year":
        start_g = today_g - timedelta(days=365)
    else:
        start_g = None

    # 🟡 اگر تاریخ شمسی دستی وارد شده، به میلادی تبدیل کن
    if start_j and end_j:
        try:
            start_g = JalaliDate.strptime(start_j, "%Y-%m-%d").to_gregorian()
            end_g = JalaliDate.strptime(end_j, "%Y-%m-%d").to_gregorian()
        except:
            end_g = today_g
    elif start_g:
        end_g = today_g
    else:
        end_g = None

    # 🧩 واکشی داده‌ها
    history_qs = PriceHistory.objects.select_related(
        "watched_url__variant__product", "watched_url__supplier"
    )

    if start_g and end_g:
        history_qs = history_qs.filter(checked_at__date__range=[start_g, end_g])

    # 🧮 گروه‌بندی آخرین و اولین قیمت در بازه
    report_data = []
    for w_id in history_qs.values_list("watched_url", flat=True).distinct():
        item_qs = history_qs.filter(watched_url_id=w_id).order_by("checked_at")
        if item_qs.count() < 2:
            continue  # فقط محصولاتی که تغییر داشتن

        first = item_qs.first()
        last = item_qs.last()

        change = last.price - first.price
        percent = round((change / first.price) * 100, 2) if first.price else 0

        report_data.append({
            "product": first.watched_url.variant.product.name,
            "supplier": first.watched_url.supplier.name,
            "old_price": first.price,
            "new_price": last.price,
            "change": change,
            "percent": percent,
            "last_checked": JalaliDate(last.checked_at).strftime("%Y-%m-%d"),
        })

    return render(request, "scrap_abdisite/price_change_report.html", {
        "report_data": report_data,
        "j_start": start_j or "",
        "j_end": end_j or "",
        "range_option": range_option or "",
    })
