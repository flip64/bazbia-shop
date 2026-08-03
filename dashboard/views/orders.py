from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.views.generic import ListView

from orders.models import Order


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class OrderListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = "dashboard/pages/orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 25

    def get_queryset(self):
        queryset = (
            Order.objects
            .select_related("customer", "customer__user")
            .annotate(items_count=Count("items"))
            .order_by("-created_at")
        )

        search = self.request.GET.get("search", "").strip()
        status = self.request.GET.get("status", "").strip()
        payment_method = self.request.GET.get(
            "payment_method",
            "",
        ).strip()
        ordering = self.request.GET.get(
            "ordering",
            "-created_at",
        ).strip()

        if search:
            search_query = Q()

            if search.isdigit():
                search_query |= Q(id=int(search))

            search_query |= Q(
                customer__phone__icontains=search
            )
            search_query |= Q(
                customer__user__first_name__icontains=search
            )
            search_query |= Q(
                customer__user__last_name__icontains=search
            )

            queryset = queryset.filter(search_query)

        if status:
            queryset = queryset.filter(status=status)

        if payment_method:
            queryset = queryset.filter(
                payment_method=payment_method
            )

        allowed_ordering = {
            "-created_at",
            "created_at",
            "-total_price",
            "total_price",
        }

        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["selected_status"] = self.request.GET.get(
            "status",
            "",
        )
        context["selected_payment_method"] = (
            self.request.GET.get("payment_method", "")
        )
        context["selected_ordering"] = self.request.GET.get(
            "ordering",
            "-created_at",
        )
        context["search_value"] = self.request.GET.get(
            "search",
            "",
        )

        context["status_choices"] = Order.STATUS_CHOICES
        context["payment_method_choices"] = (
            Order.PAYMENT_METHOD_CHOICES
        )

        return context
