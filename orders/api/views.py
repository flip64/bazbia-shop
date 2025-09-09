# orders/api/views.py
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Case, When, IntegerField
from orders.models import SalesSummary
from products.models import Product
from products.api.serializers import ProductSerializer


class WeeklyBestSellersAPIView(APIView):
    class StandardResultsSetPagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = "page_size"
        max_page_size = 50

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # آمار فروش هفته اخیر
        sales_qs = (
            SalesSummary.objects
            .filter(summary_date__range=(week_ago, today))
            .values("product_id")
            .annotate(total_sold=Sum("total_quantity"))
            .order_by("-total_sold")
        )

        product_ids = [s["product_id"] for s in sales_qs]

        if product_ids:
            # مرتب‌سازی محصولات بر اساس total_sold
            preserved_order = Case(
                *[When(id=pid, then=pos) for pos, pid in enumerate(product_ids)],
                output_field=IntegerField()
            )
            products = Product.objects.filter(id__in=product_ids).order_by(preserved_order)
        else:
            # اگر فروش هفته اخیر نبود، محصولات جدید فعال را جایگزین کن
            products = Product.objects.filter(is_active=True).order_by("-created_at")

        # pagination
        paginator = self.StandardResultsSetPagination()
        page = paginator.paginate_queryset(products, request, view=self)

        # سریالایزر
        serializer = ProductSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
