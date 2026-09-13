# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.db.models import Exists, F, OuterRef, Q, Sum
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from orders.models import Order
from products.models import Product, ProductVariant
from suppliers.models import Supplier, SupplierPriceHistory


@login_required
def dashboard_home(request):
    """
    صفحه اصلی داشبورد مدیریت بازبیا.
    """

    if not request.user.is_staff:
        raise Http404

    today = timezone.localdate()
    active_suppliers = Supplier.objects.filter(is_active=True)
    active_products = Product.objects.filter(is_active=True)

    available_variants = ProductVariant.objects.filter(
        product_id=OuterRef("pk")
    ).filter(
        Q(stock__gt=0)
        | Q(
            supplier_offers__is_available=True,
            supplier_offers__supplier_stock__gt=0,
        )
    )

    out_of_stock_count = (
        active_products
        .annotate(
            has_available_variant=Exists(available_variants)
        )
        .filter(has_available_variant=False)
        .count()
    )

    low_stock_count = (
        ProductVariant.objects
        .filter(
            product__is_active=True,
            stock__gt=0,
            stock__lte=F("low_stock_threshold"),
        )
        .exclude(
            supplier_offers__is_available=True,
            supplier_offers__supplier_stock__gt=0,
        )
        .distinct()
        .count()
    )

    today_orders = Order.objects.filter(created_at__date=today)
    paid_statuses = (
        Order.STATUS_PAID,
        Order.STATUS_SHIPPED,
        Order.STATUS_COMPLETED,
    )
    today_revenue = (
        today_orders
        .filter(status__in=paid_statuses)
        .aggregate(total=Sum("total_price"))["total"]
        or 0
    )

    recent_orders = (
        Order.objects
        .select_related("user", "shipping_address")
        .order_by("-created_at")[:7]
    )

    alerts = {
        "out_of_stock": out_of_stock_count,
        "low_stock": low_stock_count,
        "without_image": (
            active_products
            .filter(
                images__isnull=True,
                variants__images__isnull=True,
            )
            .distinct()
            .count()
        ),
        "without_category": active_products.filter(
            category__isnull=True
        ).count(),
        "zero_price": (
            active_products
            .filter(variants__price__lte=0)
            .distinct()
            .count()
        ),
    }

    context = {
        "page_title": "داشبورد مدیریت بازبیا",
        "suppliers": active_suppliers,
        "kpis": {
            "total_products": Product.objects.count(),
            "active_products": active_products.count(),
            "orders_today": today_orders.count(),
            "pending_orders": Order.objects.filter(
                status=Order.STATUS_PENDING
            ).count(),
            "today_revenue": today_revenue,
            "active_suppliers": active_suppliers.count(),
            "price_changes_today": (
                SupplierPriceHistory.objects
                .filter(created_at__date=today)
                .count()
            ),
        },
        "alerts": alerts,
        "alerts_total": sum(alerts.values()),
        "recent_orders": recent_orders,
    }

    return render(
        request,
        "dashboard/pages/home.html",
        context,
    )
