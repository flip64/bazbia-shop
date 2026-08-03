# dashboard/views/orders.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from orders.models import Order


def _staff_access_required(request):
    """
    فقط کاربران staff اجازه ورود به صفحات مدیریت سفارش‌ها را دارند.
    """

    if not request.user.is_staff:
        raise Http404


@login_required
def order_list(request):
    """
    نمایش لیست سفارش‌ها با امکان جستجو، فیلتر،
    مرتب‌سازی و صفحه‌بندی.
    """

    _staff_access_required(request)

    queryset = (
        Order.objects
        .select_related(
            "user",
            "shipping_address",
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
    selected_status = request.GET.get(
        "status",
        "",
    ).strip()

    selected_payment_method = request.GET.get(
        "payment_method",
        "",
    ).strip()

    selected_ordering = request.GET.get(
        "ordering",
        "-created_at",
    ).strip()

    if search:
        search_query = (
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
            search_query |= Q(pk=int(search))

        queryset = queryset.filter(search_query)

    valid_statuses = {
        value
        for value, label in Order.STATUS_CHOICES
    }

    if selected_status in valid_statuses:
        queryset = queryset.filter(
            status=selected_status
        )
    else:
        selected_status = ""

    valid_payment_methods = {
        value
        for value, label in Order.PAYMENT_METHOD_CHOICES
    }

    if selected_payment_method in valid_payment_methods:
        queryset = queryset.filter(
            payment_method=selected_payment_method
        )
    else:
        selected_payment_method = ""

    allowed_orderings = {
        "-created_at",
        "created_at",
        "-updated_at",
        "updated_at",
        "-total_price",
        "total_price",
    }

    if selected_ordering not in allowed_orderings:
        selected_ordering = "-created_at"

    queryset = queryset.order_by(selected_ordering)

    paginator = Paginator(queryset, 25)

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    statistics = {
        "all": Order.objects.count(),
        "pending": Order.objects.filter(
            status="pending"
        ).count(),
        "paid": Order.objects.filter(
            status="paid"
        ).count(),
        "shipped": Order.objects.filter(
            status="shipped"
        ).count(),
        "completed": Order.objects.filter(
            status="completed"
        ).count(),
        "cancelled": Order.objects.filter(
            status="cancelled"
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
    نمایش اطلاعات کامل یک سفارش شامل:
    - مشتری
    - آدرس ارسال
    - اقلام سفارش
    - مبالغ سفارش
    - وضعیت سفارش
    """

    _staff_access_required(request)

    order = get_object_or_404(
        Order.objects
        .select_related(
            "user",
            "shipping_address",
        )
        .prefetch_related(
            "items",
            "items__variant",
            "items__variant__product",
            "items__variant__attributes",
        ),
        pk=pk,
    )

    order_items = list(order.items.all())

    total_quantity = 0
    calculated_items_total = 0

    for item in order_items:
        item.line_total = item.price * item.quantity

        total_quantity += item.quantity
        calculated_items_total += item.line_total

    # اسنپ‌شات آدرس در زمان ثبت سفارش اولویت دارد.
    shipping_address_data = (
        order.shipping_address_snapshot or {}
    )

    # برای سفارش‌های قدیمی که اسنپ‌شات ندارند،
    # اطلاعات از آدرس متصل به سفارش خوانده می‌شود.
    if (
        not shipping_address_data
        and order.shipping_address
    ):
        address_object = order.shipping_address

        shipping_address_data = {
            "title": getattr(
                address_object,
                "title",
                "",
            ),
            "recipient_name": getattr(
                address_object,
                "recipient_name",
                "",
            ),
            "recipient_phone": getattr(
                address_object,
                "recipient_phone",
                "",
            ),
            "province": getattr(
                address_object,
                "province",
                "",
            ),
            "city": getattr(
                address_object,
                "city",
                "",
            ),
            "address": getattr(
                address_object,
                "address",
                "",
            ),
            "postal_code": getattr(
                address_object,
                "postal_code",
                "",
            ),
        }

    context = {
        "page_title": f"سفارش شماره {order.pk}",
        "order": order,
        "order_items": order_items,
        "total_quantity": total_quantity,
        "calculated_items_total": (
            calculated_items_total
        ),
        "shipping_address_data": (
            shipping_address_data
        ),
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

    if order.status == new_status:
        messages.info(
            request,
            "وضعیت سفارش تغییری نکرد.",
        )

        return redirect(
            "dashboard:order_detail",
            pk=order.pk,
        )

    previous_status_display = (
        order.get_status_display()
    )

    order.status = new_status
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
            f"از «{previous_status_display}» "
            f"به «{order.get_status_display()}» "
            "تغییر کرد."
        ),
    )

    return redirect(
        "dashboard:order_detail",
        pk=order.pk,
    )
