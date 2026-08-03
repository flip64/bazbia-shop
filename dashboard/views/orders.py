# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from orders.models import Order


def _staff_access_required(request):
    """
    کنترل دسترسی کاربران داشبورد.
    """
    if not request.user.is_staff:
        raise Http404


@login_required
def order_list(request):
    """
    نمایش و فیلتر فهرست سفارش‌های فروشگاه.
    """

    _staff_access_required(request)

    orders_queryset = (
        Order.objects
        .select_related(
            "user",
            "shipping_address",
            "shipping_address__customer",
        )
        .annotate(
            order_items_count=Count(
                "items",
                distinct=True,
            ),
            total_quantity=Coalesce(
                Sum("items__quantity"),
                0,
            ),
        )
    )

    search = request.GET.get("search", "").strip()
    selected_status = request.GET.get("status", "").strip()
    selected_payment_method = request.GET.get(
        "payment_method",
        "",
    ).strip()

    selected_ordering = request.GET.get(
        "ordering",
        "-created_at",
    ).strip()

    if search:
        search_filters = (
            Q(user__username__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(
                user__customer_profile__phone__icontains=search
            )
            | Q(
                shipping_address_snapshot__recipient_name__icontains=search
            )
            | Q(
                shipping_address_snapshot__recipient_phone__icontains=search
            )
        )

        if search.isdigit():
            search_filters |= Q(pk=int(search))

        orders_queryset = orders_queryset.filter(
            search_filters
        )

    valid_statuses = {
        value
        for value, label in Order.STATUS_CHOICES
    }

    if selected_status in valid_statuses:
        orders_queryset = orders_queryset.filter(
            status=selected_status
        )
    else:
        selected_status = ""

    valid_payment_methods = {
        value
        for value, label in Order.PAYMENT_METHOD_CHOICES
    }

    if selected_payment_method in valid_payment_methods:
        orders_queryset = orders_queryset.filter(
            payment_method=selected_payment_method
        )
    else:
        selected_payment_method = ""

    allowed_orderings = {
        "-created_at",
        "created_at",
        "-total_price",
        "total_price",
        "-updated_at",
        "updated_at",
    }

    if selected_ordering not in allowed_orderings:
        selected_ordering = "-created_at"

    orders_queryset = orders_queryset.order_by(
        selected_ordering
    )

    paginator = Paginator(
        orders_queryset,
        25,
    )

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    statistics = {
        "all": Order.objects.count(),
        "pending": Order.objects.filter(
            status=Order.STATUS_PENDING
        ).count(),
        "paid": Order.objects.filter(
            status=Order.STATUS_PAID
        ).count(),
        "shipped": Order.objects.filter(
            status=Order.STATUS_SHIPPED
        ).count(),
        "completed": Order.objects.filter(
            status=Order.STATUS_COMPLETED
        ).count(),
        "cancelled": Order.objects.filter(
            status=Order.STATUS_CANCELLED
        ).count(),
    }

    context = {
        "page_title": "مدیریت سفارش‌ها",
        "orders": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
        "search": search,
        "selected_status": selected_status,
        "selected_payment_method": (
            selected_payment_method
        ),
        "selected_ordering": selected_ordering,
        "status_choices": Order.STATUS_CHOICES,
        "payment_method_choices": (
            Order.PAYMENT_METHOD_CHOICES
        ),
        "statistics": statistics,
    }

    return render(
        request,
        "dashboard/pages/orders/order_list.html",
        context,
    )


@login_required
def order_detail(request, pk):
    """
    نمایش جزئیات کامل یک سفارش.
    """

    _staff_access_required(request)

    order = get_object_or_404(
        Order.objects
        .select_related(
            "user",
            "shipping_address",
            "shipping_address__customer",
        )
        .prefetch_related(
            "items",
            "items__variant",
            "items__variant__product",
        ),
        pk=pk,
    )

    context = {
        "page_title": f"سفارش شماره {order.pk}",
        "order": order,
        "status_choices": Order.STATUS_CHOICES,
    }

    return render(
        request,
        "dashboard/pages/orders/order_detail.html",
        context,
    )


@login_required
@require_POST
def order_status_update(request, pk):
    """
    تغییر وضعیت سفارش توسط مدیر.
    """

    _staff_access_required(request)

    order = get_object_or_404(
        Order,
        pk=pk,
    )

    new_status = request.POST.get(
        "status",
        "",
    ).strip()

    valid_statuses = {
        value
        for value, label in Order.STATUS_CHOICES
    }

    if new_status not in valid_statuses:
        messages.error(
            request,
            "وضعیت انتخاب‌شده معتبر نیست.",
        )

        return redirect(
            "dashboard:order_detail",
            pk=order.pk,
        )

    old_status = order.status

    if old_status == new_status:
        messages.info(
            request,
            "وضعیت سفارش تغییری نکرد.",
        )

        return redirect(
            "dashboard:order_detail",
            pk=order.pk,
        )

    order.status = new_status
    order.updated_at = timezone.now()

    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        (
            f"وضعیت سفارش شماره {order.pk} "
            f"از «{dict(Order.STATUS_CHOICES).get(old_status)}» "
            f"به «{order.get_status_display()}» تغییر کرد."
        ),
    )

    return redirect(
        "dashboard:order_detail",
        pk=order.pk,
    )
