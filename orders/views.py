from django.shortcuts import render
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum
from orders.models import SalesSummary
from products.models import Product
from products.api.serializers import ProductListSerializer





class WeeklyBestSellersAPIView(APIView):
    class StandardResultsSetPagination(PageNumberPagination):
        page_size = 10  # تعداد پیش‌فرض در هر صفحه
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
        products = Product.objects.filter(id__in=product_ids)

        if not products.exists():
            # fallback: محصولات فعال
            products = Product.objects.filter(is_active=True).order_by("-created_at")

        # pagination
        paginator = self.StandardResultsSetPagination()
        page = paginator.paginate_queryset(products, request)
        serializer = ProductListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

# Create your views here.
