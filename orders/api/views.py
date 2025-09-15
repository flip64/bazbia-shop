from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.utils.cart import CartManager
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Case, When, IntegerField
from orders.models import SalesSummary
from products.models import Product
from products.api.serializers import ProductListSerializer
from products.api.pagination import CustomCategoryPagination  # فرض می‌کنیم pagination مشترک دارید

class WeeklyBestSellersAPIView(generics.ListAPIView):

    serializer_class = ProductListSerializer
    pagination_class = CustomCategoryPagination  # استفاده از pagination مشترک

    def get_queryset(self):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # آمار فروش هفته اخیر
        sales_qs = (
            SalesSummary.objects
            .filter(created_at__date__range=(week_ago, today))  
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

        # تبدیل همه تاریخ‌ها به timezone لوکال
        for p in products:
            if timezone.is_aware(p.created_at):
                p.created_at = timezone.localtime(p.created_at)

        return products

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True, context={'request': request})
            return Response({
                "success": True,
                "count": queryset.count(),
                "data": serializer.data
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "message": "خطا در دریافت اطلاعات",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class CartView(APIView):
    """
    مدیریت کامل سبد خرید:
    - GET: نمایش آیتم‌ها
    - POST: افزودن آیتم
    - PATCH: بروزرسانی تعداد
    - DELETE: حذف آیتم یا خالی کردن سبد
    """

    def get_cart_manager(self, request):
        return CartManager(request)

    def get(self, request):
        cart_manager = self.get_cart_manager(request)
        items = [
            {
                "id": item.id,
                "variant": item.variant.id,
                "product_name": str(item.variant),
                "quantity": item.quantity,
                "price": item.price(),
                "total_price": item.total_price(),
            }
            for item in cart_manager.items()
        ]
        return Response({
            "items": items,
            "total_price": cart_manager.total_price(),
        })

    def post(self, request):
        variant_id = request.data.get("variant_id")
        quantity = int(request.data.get("quantity", 1))

        if not variant_id:
            return Response({"error": "variant_id الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        cart_manager = self.get_cart_manager(request)
        cart_manager.add(variant_id, quantity)

        return Response({"message": "محصول به سبد اضافه شد"}, status=status.HTTP_201_CREATED)

    def patch(self, request):
        variant_id = request.data.get("variant_id")
        quantity = int(request.data.get("quantity", 1))

        if not variant_id:
            return Response({"error": "variant_id الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        cart_manager = self.get_cart_manager(request)
        cart_manager.update(variant_id, quantity)

        return Response({"message": "سبد بروزرسانی شد"}, status=status.HTTP_200_OK)

    def delete(self, request):
        """
        اگر variant_id ارسال شد → حذف یک آیتم
        اگر ارسال نشد → خالی کردن کل سبد
        """
        variant_id = request.data.get("variant_id")
        cart_manager = self.get_cart_manager(request)

        if variant_id:
            cart_manager.remove(variant_id)
            return Response({"message": "آیتم حذف شد"}, status=status.HTTP_200_OK)
        else:
            cart_manager.clear()
            return Response({"message": "سبد خرید خالی شد"}, status=status.HTTP_200_OK)
