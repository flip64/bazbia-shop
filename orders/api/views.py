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


# ==============================
# 🔥 بهترین فروش‌های هفته
# ==============================
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

        # تبدیل timezone برای created_at
        for p in products:
            if getattr(p, 'created_at', None) and timezone.is_aware(p.created_at):
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


# ==============================
# 🛒 سبد خرید
# ==============================
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

    # ==========================
    # 🔹 گرفتن URL تصویر واریانت/محصول
    # ==========================
    def get_image_url(self, variant, product):
        try:
            main_image = variant.images.filter(is_main=True).first()
            if not main_image:
                main_image = product.images.filter(is_main=True).first()
            if not main_image and product.images.exists():
                main_image = product.images.first()
            return main_image.image.url if main_image else None
        except Exception:
            return None

    # ==========================
    # 🔹 GET آیتم‌ها
    # ==========================
    def get(self, request):
        cart_manager = self.get_cart_manager(request)
        items = []

        for item in cart_manager.items():
            variant = getattr(item, "variant", None)
            product = getattr(variant, "product", None)

            if not variant or not product:
                continue

            image_url = self.get_image_url(variant, product)

            # ترکیب نام محصول + attributes
            variant_attributes = ", ".join([str(av) for av in variant.attributes.all()])
            product_name = f"{product.name} ({variant_attributes})" if variant_attributes else product.name

            items.append({
                "id": item.id,
                "variant": variant.id,
                "product_name": product_name,
                "quantity": item.quantity,
                "price": item.price(),
                "total_price": item.total_price,
                "image": request.build_absolute_uri(image_url) if image_url else None,
            })

        return Response({
            "success": True,
            "items": items,
            "total_price": cart_manager.total_price(),
        })

    # ==========================
    # 🔹 افزودن محصول
    # ==========================
    def post(self, request):
        variant_id = request.data.get("variant_id")
        try:
            quantity = int(request.data.get("quantity", 1))
        except ValueError:
            return Response({"success": False, "error": "quantity باید عدد باشد"}, status=status.HTTP_400_BAD_REQUEST)

        if not variant_id:
            return Response({"success": False, "error": "variant_id الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        cart_manager = self.get_cart_manager(request)
        cart_manager.add(variant_id, quantity)

        return Response({"success": True, "message": "محصول به سبد اضافه شد"}, status=status.HTTP_201_CREATED)

    # ==========================
    # 🔹 بروزرسانی تعداد
    # ==========================
    def patch(self, request):
        variant_id = request.data.get("variant_id")
        try:
            quantity = int(request.data.get("quantity", 1))
        except ValueError:
            return Response({"success": False, "error": "quantity باید عدد باشد"}, status=status.HTTP_400_BAD_REQUEST)

        if not variant_id:
            return Response({"success": False, "error": "variant_id الزامی است"}, status=status.HTTP_400_BAD_REQUEST)

        cart_manager = self.get_cart_manager(request)
        cart_manager.update(variant_id, quantity)

        return Response({"success": True, "message": "سبد بروزرسانی شد"}, status=status.HTTP_200_OK)

    # ==========================
    # 🔹 حذف محصول یا خالی کردن سبد
    # ==========================
    def delete(self, request):
        variant_id = request.data.get("variant_id")
        cart_manager = self.get_cart_manager(request)

        if variant_id:
            cart_manager.remove(variant_id)
            return Response({"success": True, "message": "آیتم حذف شد"}, status=status.HTTP_200_OK)
        else:
            cart_manager.clear()
            return Response({"success": True, "message": "سبد خرید خالی شد"}, status=status.HTTP_200_OK)
