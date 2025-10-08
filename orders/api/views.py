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
from products.api.pagination import CustomCategoryPagination


# ===========================
# Weekly Best Sellers API
# ===========================
class WeeklyBestSellersAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = CustomCategoryPagination

    def get_queryset(self):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        sales_qs = (
            SalesSummary.objects
            .filter(created_at__date__range=(week_ago, today))
            .values("product_id")
            .annotate(total_sold=Sum("total_quantity"))
            .order_by("-total_sold")
        )

        product_ids = [s["product_id"] for s in sales_qs]

        if product_ids:
            preserved_order = Case(
                *[When(id=pid, then=pos) for pos, pid in enumerate(product_ids)],
                output_field=IntegerField()
            )
            products = Product.objects.filter(id__in=product_ids).order_by(preserved_order)
        else:
            products = Product.objects.filter(is_active=True).order_by("-created_at")

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


# ===========================
# Cart API
# ===========================
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

    # -------------------------
    # نمایش سبد
    # -------------------------
    def get(self, request):
        cart_manager = self.get_cart_manager(request)
        items = []

        for item in cart_manager.items():
            variant = item.variant
            product = variant.product

            # انتخاب تصویر مناسب
            image_url = None
            variant_main_image = variant.images.filter(is_main=True).first()
            if variant_main_image and variant_main_image.image:
                image_url = variant_main_image.image.url
            elif product.images.filter(is_main=True).exists():
                image_url = product.images.filter(is_main=True).first().image.url
            elif product.images.exists():
                image_url = product.images.first().image.url

            price = variant.discount_price or variant.price  # استفاده از قیمت تخفیف

            items.append({
                "id": item.id,
                "variant": variant.id,
                "product_name": str(variant),
                "quantity": item.quantity,
                "price": price,
                "total_price": price * item.quantity,
                "image": request.build_absolute_uri(image_url) if image_url else None,
            })

        return Response({
            "items": items,
            "total_price": cart_manager.total_price(),
        })

    # -------------------------
    # افزودن به سبد
    # -------------------------
    def post(self, request):
        variant_id = request.data.get("variant_id")
        quantity = int(request.data.get("quantity", 1))

        if not variant_id:
            return Response({"error": "variant_id الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        cart_manager = self.get_cart_manager(request)
        cart_manager.add(variant_id, quantity)

        return Response({"message": "محصول به سبد اضافه شد"}, status=status.HTTP_201_CREATED)

    # -------------------------
    # بروزرسانی تعداد
    # -------------------------
    def patch(self, request):
        variant_id = request.data.get("variant_id")
        quantity = int(request.data.get("quantity", 1))

        if not variant_id:
            return Response({"error": "variant_id الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        cart_manager = self.get_cart_manager(request)
        cart_manager.update(variant_id, quantity)

        return Response({"message": "سبد بروزرسانی شد"}, status=status.HTTP_200_OK)

    # -------------------------
    # حذف آیتم یا خالی کردن سبد
    # -------------------------
    def delete(self, request):
        variant_id = request.data.get("variant_id")
        cart_manager = self.get_cart_manager(request)

        if variant_id:
            cart_manager.remove(variant_id)
            return Response({"message": "آیتم حذف شد"}, status=status.HTTP_200_OK)
        else:
            cart_manager.clear()
            return Response({"message": "سبد خرید خالی شد"}, status=status.HTTP_200_OK)
